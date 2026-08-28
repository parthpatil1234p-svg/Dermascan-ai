import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.core.config import Settings
from app.core.model_input_config import get_model_input_contract

EXPECTED_CLASSES = ("normal", "oily", "dry", "combination")


class ModelLoadError(Exception):
    pass


class ModelUnavailableError(ModelLoadError):
    pass


class ModelMetadataError(ModelLoadError):
    pass


@dataclass(frozen=True)
class SkinTypeModelBundle:
    model: Any
    metadata: dict[str, Any]
    class_map: dict[int, str]


def read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelMetadataError from exc
    if not isinstance(payload, dict):
        raise ModelMetadataError
    return payload


def validate_class_map(raw: dict[str, Any]) -> dict[int, str]:
    try:
        class_map = {int(index): str(label).lower() for index, label in raw.items()}
        ordered = tuple(class_map[index] for index in range(len(class_map)))
    except (KeyError, TypeError, ValueError) as exc:
        raise ModelMetadataError from exc
    if ordered != EXPECTED_CLASSES:
        raise ModelMetadataError
    return class_map


def validate_metadata(metadata: dict[str, Any], settings: Settings) -> None:
    contract = get_model_input_contract(settings)
    expected = {
        "input_width": contract.width,
        "input_height": contract.height,
        "input_channels": contract.channels,
        "colour_space": contract.colour_space,
        "normalization": contract.normalization,
        "resize_mode": contract.resize_mode,
        "classes": list(EXPECTED_CLASSES),
    }
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise ModelMetadataError
    if not metadata.get("model_name") or not metadata.get("model_version"):
        raise ModelMetadataError


def normalize_shape(shape: Any) -> tuple[Any, ...]:
    if isinstance(shape, list) and shape and isinstance(shape[0], (list, tuple)):
        shape = shape[0]
    return tuple(shape)


def validate_model_shapes(model: Any, settings: Settings) -> None:
    input_shape = normalize_shape(model.input_shape)
    output_shape = normalize_shape(model.output_shape)
    expected_input = (
        None,
        settings.model_input_height,
        settings.model_input_width,
        settings.model_input_channels,
    )
    if input_shape != expected_input or output_shape != (None, len(EXPECTED_CLASSES)):
        raise ModelMetadataError


def load_skin_type_model_bundle(
    settings: Settings,
    load_function: Callable[[Path], Any] | None = None,
) -> SkinTypeModelBundle:
    required = (
        settings.skin_type_model_path,
        settings.skin_type_metadata_path,
        settings.skin_type_class_map_path,
    )
    if not all(path.is_file() for path in required):
        raise ModelUnavailableError
    metadata = read_json(settings.skin_type_metadata_path)
    class_map = validate_class_map(read_json(settings.skin_type_class_map_path))
    validate_metadata(metadata, settings)
    if load_function is None:
        try:
            from tensorflow.keras.models import load_model
        except ImportError as exc:
            raise ModelUnavailableError from exc
        load_function = load_model
    try:
        model = load_function(settings.skin_type_model_path)
    except Exception as exc:
        raise ModelLoadError from exc
    validate_model_shapes(model, settings)
    return SkinTypeModelBundle(model=model, metadata=metadata, class_map=class_map)
