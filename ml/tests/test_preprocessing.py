import numpy as np
from PIL import Image

from src.augmentation import augment_training_image, prepare_validation_image
from src.preprocessing import letterbox_rgb, normalize_zero_to_one


def test_training_preprocessing_shape() -> None:
    image = Image.new("RGB", (320, 480), (100, 120, 140))
    assert letterbox_rgb(image).shape == (224, 224, 3)


def test_validation_preprocessing_shape() -> None:
    image = Image.new("L", (480, 320), 100)
    assert letterbox_rgb(image).shape == (224, 224, 3)


def test_zero_to_one_normalization() -> None:
    tensor = normalize_zero_to_one(np.array([[[0, 127, 255]]], dtype=np.uint8))
    assert tensor.dtype == np.float32
    assert tensor.min() == 0.0
    assert tensor.max() == 1.0


def test_training_only_augmentation() -> None:
    image = np.arange(12 * 12 * 3, dtype=np.uint8).reshape(12, 12, 3)
    rng = np.random.default_rng(42)
    assert not np.array_equal(augment_training_image(image, rng), image)
    assert np.array_equal(prepare_validation_image(image), image)
