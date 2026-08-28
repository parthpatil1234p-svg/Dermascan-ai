from datetime import datetime, timezone
from typing import Any

from src.concern_labels import CONCERN_LABELS


def generate_concern_metadata(
    config: dict[str, Any],
    metrics: dict[str, Any],
    thresholds: dict[str, float],
    dataset_version: str,
) -> dict[str, Any]:
    return {
        "model_name": "DermaScan Visible Skin Concern Classifier",
        "model_version": "1.0.0",
        "architecture": config["model"]["architecture"],
        "input_width": config["input"]["width"],
        "input_height": config["input"]["height"],
        "input_channels": config["input"]["channels"],
        "colour_space": config["input"]["colour_space"],
        "normalization": config["input"]["normalization"],
        "resize_mode": config["input"]["resize_mode"],
        "output_activation": "sigmoid",
        "labels": list(CONCERN_LABELS),
        "thresholds": thresholds,
        "threshold_source": "validation_f1_tuning",
        "training_date": datetime.now(timezone.utc).isoformat(),
        "dataset_version": dataset_version,
        "metrics": metrics,
    }
