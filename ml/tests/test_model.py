import json
from pathlib import Path

import numpy as np
import pytest

from scripts.generate_model_metadata import generate_metadata
from scripts.export_skin_type_model import validate_export_metrics
from src.calibration import expected_calibration_error
from src.metrics import classification_metrics
from src.model import build_skin_type_model
from src.utils import load_class_map


def test_class_map_consistency() -> None:
    path = Path(__file__).resolve().parents[1] / "configs/class_map.json"
    assert load_class_map(path) == {0: "normal", 1: "oily", 2: "dry", 3: "combination"}


def test_model_rejects_non_rgb_shape() -> None:
    with pytest.raises(ValueError):
        build_skin_type_model((224, 224, 1), 4, 0.3)


def test_evaluation_metric_calculation() -> None:
    labels = np.array([0, 1, 2, 3])
    probabilities = np.eye(4, dtype=np.float32)
    metrics = classification_metrics(labels, probabilities)
    assert metrics["accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["confusion_matrix"] == np.eye(4, dtype=int).tolist()


def test_calibration_error_is_finite() -> None:
    labels = np.array([0, 1])
    probabilities = np.array([[0.8, 0.2], [0.4, 0.6]])
    assert np.isfinite(expected_calibration_error(labels, probabilities))


def test_metadata_generation_has_no_invented_metrics() -> None:
    config = {
        "input": {"width": 224, "height": 224, "channels": 3, "colour_space": "RGB", "normalization": "zero_to_one", "resize_mode": "letterbox"},
        "model": {"architecture": "MobileNetV2"},
    }
    metadata = generate_metadata(config, {}, "licensed-dataset-v1")
    assert metadata["classes"] == ["normal", "oily", "dry", "combination"]
    assert metadata["metrics"] == {}


def test_export_rejects_placeholder_metrics() -> None:
    assert validate_export_metrics({"accuracy": 0.0}) is False


def test_tensorflow_model_output_and_reload(tmp_path: Path) -> None:
    tf = pytest.importorskip("tensorflow")
    model = build_skin_type_model((224, 224, 3), 4, 0.3, pretrained_weights=None)
    output = model(np.zeros((1, 224, 224, 3), dtype=np.float32), training=False).numpy()
    assert output.shape == (1, 4)
    assert output.sum() == pytest.approx(1.0)
    model_path = tmp_path / "model.keras"
    model.save(model_path)
    assert tf.keras.models.load_model(model_path).output_shape == (None, 4)
