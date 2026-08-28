import numpy as np

from scripts.calibrate_concern_thresholds import build_threshold_payload
from src.concern_labels import CONCERN_LABELS
from src.concern_thresholds import apply_per_label_thresholds, tune_per_label_thresholds


def test_per_label_threshold_application() -> None:
    result = apply_per_label_thresholds(np.array([0.6, 0.4]), {"a": 0.5, "b": 0.3}, ("a", "b"))
    assert result.tolist() == [1, 1]


def test_threshold_generation_uses_validation_scores() -> None:
    targets = np.array([[0, 1], [1, 0], [1, 1], [0, 0]], dtype=np.float32)
    mask = np.ones_like(targets)
    scores = np.array([[0.1, 0.8], [0.9, 0.2], [0.7, 0.7], [0.2, 0.1]])
    thresholds, report = tune_per_label_thresholds(targets, mask, scores, ("a", "b"))
    assert set(thresholds) == {"a", "b"}
    assert report["a"]["validation_f1"] == 1.0


def test_threshold_file_payload_is_calibrated_and_complete() -> None:
    thresholds = {label: 0.5 for label in CONCERN_LABELS}
    payload = build_threshold_payload(thresholds)
    assert payload["source"] == "validation_f1_tuning"
    assert payload["calibrated"] is True
    assert payload["thresholds"] == thresholds
