from dataclasses import asdict, dataclass
from typing import Any

from app.core.config import Settings


@dataclass(frozen=True)
class ModelInputContract:
    width: int
    height: int
    channels: int
    colour_space: str
    data_type: str
    normalization: str
    pixel_range: tuple[float, float]
    resize_mode: str
    channel_order: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_model_input_contract(settings: Settings) -> ModelInputContract:
    return ModelInputContract(
        width=settings.model_input_width,
        height=settings.model_input_height,
        channels=settings.model_input_channels,
        colour_space=settings.model_input_colour_space,
        data_type="float32",
        normalization=settings.preprocess_normalization_mode,
        pixel_range=(0.0, 1.0),
        resize_mode=settings.preprocess_resize_mode,
        channel_order="RGB",
    )
