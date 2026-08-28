import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.core.config import Settings
from app.core.model_input_config import get_model_input_contract
from app.core.skin_concern_labels import CONCERN_LABELS


class ConcernModelLoadError(Exception):
    pass


class ConcernModelUnavailableError(ConcernModelLoadError):
    pass


class ConcernModelMetadataError(ConcernModelLoadError):
    pass


@dataclass(frozen=True)
class SkinConcernModelBundle:
    model: Any
    metadata: dict[str, Any]
    label_map: dict[int, str]
    thresholds: dict[str, float]
    thresholds_calibrated: bool


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConcernModelMetadataError from exc
    if not isinstance(payload, dict):
        raise ConcernModelMetadataError
    return payload


def validate_concern_label_map(raw: dict[str, Any]) -> dict[int, str]:
    try:
        result = {int(index): str(label) for index, label in raw.items()}
        ordered = tuple(result[index] for index in range(len(result)))
    except (KeyError, TypeError, ValueError) as exc:
        raise ConcernModelMetadataError from exc
    if ordered != CONCERN_LABELS:
        raise ConcernModelMetadataError
    return result


def validate_concern_metadata(metadata: dict[str, Any], settings: Settings) -> None:
    contract = get_model_input_contract(settings)
    expected = {
        "input_width": contract.width,
        "input_height": contract.height,
        "input_channels": contract.channels,
        "colour_space": contract.colour_space,
        "normalization": contract.normalization,
        "resize_mode": contract.resize_mode,
        "output_activation": "sigmoid",
        "labels": list(CONCERN_LABELS),
        "threshold_source": "validation_f1_tuning",
    }
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise ConcernModelMetadataError
    required_text = (
        "model_name",
        "model_version",
        "architecture",
        "training_date",
        "dataset_version",
    )
    if any(
        not isinstance(metadata.get(key), str) or not metadata[key].strip() for key in required_text
    ):
        raise ConcernModelMetadataError
    if not isinstance(metadata.get("metrics"), dict) or not metadata["metrics"]:
        raise ConcernModelMetadataError


def validate_concern_thresholds(raw: dict[str, Any]) -> tuple[dict[str, float], bool]:
    thresholds = raw.get("thresholds")
    if not isinstance(thresholds, dict) or set(thresholds) != set(CONCERN_LABELS):
        raise ConcernModelMetadataError
    try:
        parsed = {label: float(thresholds[label]) for label in CONCERN_LABELS}
    except (TypeError, ValueError) as exc:
        raise ConcernModelMetadataError from exc
    if any(value <= 0 or value >= 1 for value in parsed.values()):
        raise ConcernModelMetadataError
    if raw.get("calibrated") is not True or raw.get("source") != "validation_f1_tuning":
        raise ConcernModelMetadataError
    return parsed, True


def normalize_shape(shape: Any) -> tuple[Any, ...]:
    if isinstance(shape, list) and shape and isinstance(shape[0], (list, tuple)):
        shape = shape[0]
    return tuple(shape)


def validate_concern_model_shapes(model: Any, settings: Settings) -> None:
    expected_input = (
        None,
        settings.model_input_height,
        settings.model_input_width,
        settings.model_input_channels,
    )
    if normalize_shape(model.input_shape) != expected_input:
        raise ConcernModelMetadataError
    if normalize_shape(model.output_shape) != (None, len(CONCERN_LABELS)):
        raise ConcernModelMetadataError


def load_skin_concern_model_bundle(
    settings: Settings,
    load_function: Callable[[Path], Any] | None = None,
) -> SkinConcernModelBundle:
    required = (
        settings.skin_concern_model_path,
        settings.skin_concern_metadata_path,
        settings.skin_concern_label_map_path,
        settings.skin_concern_thresholds_path,
    )
    if not all(path.is_file() for path in required):
        raise ConcernModelUnavailableError
    metadata = read_json_object(settings.skin_concern_metadata_path)
    label_map = validate_concern_label_map(read_json_object(settings.skin_concern_label_map_path))
    thresholds, calibrated = validate_concern_thresholds(
        read_json_object(settings.skin_concern_thresholds_path)
    )
    validate_concern_metadata(metadata, settings)
    if metadata.get("thresholds") != thresholds:
        raise ConcernModelMetadataError
    if load_function is None:
        try:
            from tensorflow.keras.models import load_model
        except ImportError as exc:
            raise ConcernModelUnavailableError from exc
        load_function = load_model
    try:
        model = load_function(settings.skin_concern_model_path)
    except Exception as exc:
        raise ConcernModelLoadError from exc
    validate_concern_model_shapes(model, settings)
    return SkinConcernModelBundle(
        model=model,
        metadata=metadata,
        label_map=label_map,
        thresholds=thresholds,
        thresholds_calibrated=calibrated,
    )
