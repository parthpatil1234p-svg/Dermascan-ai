import numpy as np
import pytest

from scripts.export_skin_concern_model import artifacts_are_exportable
from scripts.generate_concern_model_metadata import generate_concern_metadata
from scripts.train_skin_concern_model import concern_augmentation_policy
from src.concern_labels import CONCERN_LABELS
from src.concern_model import build_skin_concern_model


def test_model_rejects_non_rgb_shape() -> None:
    with pytest.raises(ValueError):
        build_skin_concern_model((224, 224, 1), 10, 0.3)


def test_metadata_generation_has_fixed_labels_and_no_invented_metrics() -> None:
    config = {
        "input": {"width": 224, "height": 224, "channels": 3, "colour_space": "RGB", "normalization": "zero_to_one", "resize_mode": "letterbox"},
        "model": {"architecture": "MobileNetV2"},
    }
    metadata = generate_concern_metadata(config, {}, {}, "dataset-v1")
    assert metadata["labels"] == list(CONCERN_LABELS)
    assert metadata["metrics"] == {}


def test_export_rejects_placeholder_artifacts() -> None:
    assert artifacts_are_exportable({"macro_f1": 0.0}, {"calibrated": False}) is False


def test_training_augmentation_policy_is_conservative() -> None:
    policy = concern_augmentation_policy(
        {
            "augmentation": {
                "horizontal_flip": True,
                "rotation_degrees": 8,
                "translation_fraction": 0.05,
                "zoom_fraction": 0.10,
                "brightness_fraction": 0.08,
                "contrast_fraction": 0.08,
            }
        }
    )
    assert policy["rotation_degrees"] <= 8
    assert policy["translation_fraction"] <= 0.05
    assert policy["brightness_fraction"] <= 0.08
    assert not ({"blur", "skin_smoothing", "random_erasing"} & set(policy))


def test_tensorflow_sigmoid_shape_range_and_reload(tmp_path) -> None:
    tf = pytest.importorskip("tensorflow")
    model = build_skin_concern_model((224, 224, 3), 10, 0.3, pretrained_weights=None)
    values = model(np.zeros((1, 224, 224, 3), dtype=np.float32), training=False).numpy()
    assert values.shape == (1, 10)
    assert ((values >= 0) & (values <= 1)).all()
    path = tmp_path / "concern.keras"
    model.save(path)
    assert tf.keras.models.load_model(path).output_shape == (None, 10)
