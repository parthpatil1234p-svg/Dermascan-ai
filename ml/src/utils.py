import json
from pathlib import Path
from typing import Any

import yaml

from src import CLASS_NAMES


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("Training configuration must be a mapping.")
    return config


def load_class_map(path: Path) -> dict[int, str]:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    class_map = {int(index): str(label) for index, label in raw.items()}
    if tuple(class_map[index] for index in sorted(class_map)) != CLASS_NAMES:
        raise ValueError("Class map does not match the canonical class order.")
    return class_map


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
