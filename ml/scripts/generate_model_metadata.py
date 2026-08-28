from datetime import datetime, timezone
from typing import Any

from src import CLASS_NAMES


def generate_metadata(config: dict[str, Any], metrics: dict[str, Any], dataset_version: str) -> dict[str, Any]:
    return {
        "model_name": "DermaScan Skin Type Classifier",
        "model_version": "1.0.0",
        "architecture": config["model"]["architecture"],
        "input_width": config["input"]["width"],
        "input_height": config["input"]["height"],
        "input_channels": config["input"]["channels"],
        "colour_space": config["input"]["colour_space"],
        "normalization": config["input"]["normalization"],
        "resize_mode": config["input"]["resize_mode"],
        "classes": list(CLASS_NAMES),
        "training_date": datetime.now(timezone.utc).isoformat(),
        "dataset_version": dataset_version,
        "metrics": metrics,
    }
