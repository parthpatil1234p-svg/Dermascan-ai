import numpy as np


def augment_training_image(image: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    output = image.copy()
    if rng.random() < 0.5:
        output = np.fliplr(output)
    brightness = rng.uniform(0.92, 1.08)
    contrast = rng.uniform(0.92, 1.08)
    mean = output.mean(axis=(0, 1), keepdims=True)
    output = (output.astype(np.float32) - mean) * contrast + mean
    return np.clip(output * brightness, 0, 255).astype(np.uint8)


def prepare_validation_image(image: np.ndarray) -> np.ndarray:
    return image.copy()
