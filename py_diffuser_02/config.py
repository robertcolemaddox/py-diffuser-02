"""Application configuration.

Keep user-facing generation settings here rather than scattering them through
the application code.
"""

from pathlib import Path

APP_NAME = "Py Diffuser 02"
APP_VERSION = "0.2.0"

# Stable Diffusion model
SD_MODEL_ID = "runwayml/stable-diffusion-v1-5"
NUM_INFERENCE_STEPS = 30
GUIDANCE_SCALE = 7.5

# Image output
BASE_WIDTH = 1280
BASE_HEIGHT = 720
UPSCALE_TO_4K = True
UPSCALE_WIDTH = 3840
UPSCALE_HEIGHT = 2160

# Video output
VIDEO_NUM_FRAMES = 12
VIDEO_FPS = 6
VIDEO_WIDTH = 512
VIDEO_HEIGHT = 512

# Prompt enhancement
USE_OLLAMA = True
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"
MAX_PROMPT_CHARS = 150

# Photorealism is intentionally not user-selectable.
PHOTOREALISTIC_SYSTEM_PROMPT = (
    "Rewrite this image prompt as a concise description of a realistic photograph. "
    "Focus on concrete visual details, natural lighting, camera perspective, "
    "materials, depth, and colors. Avoid metaphors and overly flowery language. "
    "Keep under 60 words."
)

PHOTOREALISTIC_NEGATIVE_PROMPT = (
    "painting, illustration, anime, cartoon, abstract, psychedelic, surreal, "
    "oil painting, brush strokes, art style, distorted, blurry, lowres, "
    "low resolution, logo, watermark, text, caption"
)

# Img2Img
IMG2IMG_STRENGTH = 0.6

# Output location is beside the executable/source package.
OUTPUT_DIRECTORY_NAME = "output"


def get_output_directory() -> Path:
    """Return/create the application's output directory."""
    directory = Path(__file__).resolve().parent.parent / OUTPUT_DIRECTORY_NAME
    directory.mkdir(parents=True, exist_ok=True)
    return directory
