"""Image and video generation services."""

import datetime as dt
import threading
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image

from . import config
from .ollama_client import enhance_prompt


class GenerationService:
    """Generate photorealistic images and short frame-sequence videos."""

    def __init__(self, model_manager, log_func, set_status):
        self.model_manager = model_manager
        self.log = log_func
        self.set_status = set_status
        self.progress = {"value": 0}
        self.is_generating = False

    def generate_image_async(self, prompt, on_finished, init_image_path=None):
        threading.Thread(
            target=self._generate_image,
            args=(prompt, on_finished, init_image_path),
            daemon=True,
        ).start()

    def _generate_image(self, prompt, on_finished, init_image_path):
        self.is_generating = True
        self.progress["value"] = 0

        try:
            if not self.model_manager.loaded:
                raise RuntimeError(
                    self.model_manager.error or "Stable Diffusion model is not loaded."
                )

            sd_prompt = enhance_prompt(prompt, self.log)
            use_img2img = init_image_path is not None

            self.set_status(
                "Generating edited image..."
                if use_img2img
                else "Generating photorealistic image..."
            )
            self.log("Final Stable Diffusion prompt:")
            self.log(sd_prompt)

            def callback(step, timestep, latents):
                self.progress["value"] = int(
                    100 * (step + 1) / config.NUM_INFERENCE_STEPS
                )

            kwargs = {
                "prompt": sd_prompt,
                "num_inference_steps": config.NUM_INFERENCE_STEPS,
                "guidance_scale": config.GUIDANCE_SCALE,
                "negative_prompt": config.PHOTOREALISTIC_NEGATIVE_PROMPT,
                "callback": callback,
                "callback_steps": 1,
            }

            if use_img2img:
                image_path = Path(init_image_path)
                if not image_path.is_file():
                    raise FileNotFoundError(f"Init image not found: {image_path}")

                init_image = Image.open(image_path).convert("RGB")
                init_image = init_image.resize(
                    (config.BASE_WIDTH, config.BASE_HEIGHT), Image.LANCZOS
                )

                result = self.model_manager.get_img2img_pipeline()(
                    image=init_image,
                    strength=config.IMG2IMG_STRENGTH,
                    **kwargs,
                )
            else:
                result = self.model_manager.pipeline(
                    height=config.BASE_HEIGHT,
                    width=config.BASE_WIDTH,
                    **kwargs,
                )

            image = result.images[0]

            if config.UPSCALE_TO_4K:
                self.log(
                    f"Upscaling to {config.UPSCALE_WIDTH}x{config.UPSCALE_HEIGHT}..."
                )
                image = image.resize(
                    (config.UPSCALE_WIDTH, config.UPSCALE_HEIGHT), Image.LANCZOS
                )

            timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = "edit" if use_img2img else "gen"
            filename = (
                config.get_output_directory()
                / f"pydiffuser02_photo_{suffix}_{image.width}x{image.height}_{timestamp}.png"
            )
            image.save(filename)

            self.progress["value"] = 100
            self.set_status(f"Done. Saved image: {filename.name}")
            self.log(f"Image saved to: {filename}")

        except Exception as exc:
            self.set_status("Error during image generation.")
            self.log(f"Error generating image: {exc}")

        finally:
            self.is_generating = False
            on_finished()

    def generate_video_async(self, prompt, on_finished):
        threading.Thread(
            target=self._generate_video,
            args=(prompt, on_finished),
            daemon=True,
        ).start()

    def _generate_video(self, prompt, on_finished):
        self.is_generating = True
        self.progress["value"] = 0

        try:
            if not self.model_manager.loaded:
                raise RuntimeError(
                    self.model_manager.error or "Stable Diffusion model is not loaded."
                )

            sd_prompt = enhance_prompt(prompt, self.log)
            self.set_status("Generating photorealistic video frames...")
            self.log("Final Stable Diffusion prompt:")
            self.log(sd_prompt)

            frames = []

            for frame_index in range(config.VIDEO_NUM_FRAMES):
                self.log(
                    f"Generating frame {frame_index + 1}/{config.VIDEO_NUM_FRAMES}..."
                )

                def make_callback(current_frame_index):
                    def callback(step, timestep, latents):
                        frame_progress = (
                            (step + 1) / config.NUM_INFERENCE_STEPS
                        )
                        overall = (
                            current_frame_index + frame_progress
                        ) / config.VIDEO_NUM_FRAMES
                        self.progress["value"] = int(100 * overall)

                    return callback

                result = self.model_manager.pipeline(
                    sd_prompt,
                    num_inference_steps=config.NUM_INFERENCE_STEPS,
                    guidance_scale=config.GUIDANCE_SCALE,
                    negative_prompt=config.PHOTOREALISTIC_NEGATIVE_PROMPT,
                    height=config.VIDEO_HEIGHT,
                    width=config.VIDEO_WIDTH,
                    callback=make_callback(frame_index),
                    callback_steps=1,
                )

                frames.append(np.array(result.images[0]))

            timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = (
                config.get_output_directory()
                / f"pydiffuser02_photo_video_{config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}_"
                f"{config.VIDEO_NUM_FRAMES}f_{timestamp}.mp4"
            )

            self.log(
                f"Encoding {len(frames)} frames to MP4 at {config.VIDEO_FPS} FPS..."
            )
            with imageio.get_writer(filename, fps=config.VIDEO_FPS) as writer:
                for frame in frames:
                    writer.append_data(frame)

            self.progress["value"] = 100
            self.set_status(f"Done. Saved video: {filename.name}")
            self.log(f"Video saved to: {filename}")

        except Exception as exc:
            self.set_status("Error during video generation.")
            self.log(f"Error generating video: {exc}")

        finally:
            self.is_generating = False
            on_finished()
