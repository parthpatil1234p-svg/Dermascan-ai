import numpy as np
from PIL import Image


def letterbox_rgb(image: Image.Image, width: int = 224, height: int = 224) -> np.ndarray:
    rgb = image.convert("RGB")
    scale = min(width / rgb.width, height / rgb.height)
    resized_size = (max(1, round(rgb.width * scale)), max(1, round(rgb.height * scale)))
    resized = rgb.resize(resized_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (width, height), (127, 127, 127))
    canvas.paste(resized, ((width - resized.width) // 2, (height - resized.height) // 2))
    return np.asarray(canvas, dtype=np.uint8)


def normalize_zero_to_one(image: np.ndarray) -> np.ndarray:
    if image.dtype != np.uint8:
        raise ValueError("Training preprocessing expects 8-bit input.")
    return image.astype(np.float32) / 255.0
