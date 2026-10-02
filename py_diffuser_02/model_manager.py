"""Stable Diffusion model and pipeline management."""

import threading

import torch
from diffusers import (
    DPMSolverMultistepScheduler,
    StableDiffusionImg2ImgPipeline,
    StableDiffusionPipeline,
)

from . import config


class ModelManager:
    """Owns the text-to-image and lazily-loaded img2img pipelines."""

    def __init__(self, log_func, set_status):
        self.log = log_func
        self.set_status = set_status
        self.pipeline = None
        self.img2img_pipeline = None
        self.loaded = False
        self.error = None

    @property
    def device(self) -> str:
        return "cuda" if torch.cuda.is_available() else "cpu"

    @property
    def dtype(self):
        return torch.float16 if self.device == "cuda" else torch.float32

    def load_async(self) -> None:
        """Load the main pipeline without freezing Tkinter."""
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self) -> None:
        try:
            self.set_status("Loading Stable Diffusion model...")
            self.log(f"Loading model: {config.SD_MODEL_ID}")
            self.log(f"Device: {self.device}")

            pipeline = StableDiffusionPipeline.from_pretrained(
                config.SD_MODEL_ID,
                torch_dtype=self.dtype,
            )
            pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
                pipeline.scheduler.config
            )

            if self.device == "cuda":
                pipeline = pipeline.to("cuda")

            pipeline.enable_attention_slicing()
            try:
                pipeline.enable_vae_slicing()
            except Exception:
                pass

            # Preserves the behavior of the original application.
            pipeline.safety_checker = None

            self.pipeline = pipeline
            self.loaded = True
            self.error = None

            self.set_status("Model loaded. Ready.")
            self.log("Model loaded successfully.")
            self.log(
                f"Image base resolution: {config.BASE_WIDTH}x{config.BASE_HEIGHT}"
            )
            if config.UPSCALE_TO_4K:
                self.log(
                    f"Image upscale: {config.BASE_WIDTH}x{config.BASE_HEIGHT} -> "
                    f"{config.UPSCALE_WIDTH}x{config.UPSCALE_HEIGHT}"
                )
            self.log(
                f"Video: {config.VIDEO_NUM_FRAMES} frames @ {config.VIDEO_FPS} FPS, "
                f"{config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}"
            )

        except Exception as exc:
            self.error = str(exc)
            self.loaded = False
            self.set_status("Error loading model.")
            self.log(f"Error loading model: {exc}")

    def get_img2img_pipeline(self):
        """Load the img2img pipeline only when image editing is requested."""
        if self.img2img_pipeline is not None:
            return self.img2img_pipeline

        try:
            self.log("Loading img2img pipeline for image editing...")

            pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
                config.SD_MODEL_ID,
                torch_dtype=self.dtype,
            )
            pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
                pipeline.scheduler.config
            )

            if self.device == "cuda":
                pipeline = pipeline.to("cuda")

            pipeline.enable_attention_slicing()
            try:
                pipeline.enable_vae_slicing()
            except Exception:
                pass

            pipeline.safety_checker = None

            self.img2img_pipeline = pipeline
            self.log("Img2img pipeline loaded.")
            return pipeline

        except Exception as exc:
            self.log(f"Error loading img2img pipeline: {exc}")
            raise
