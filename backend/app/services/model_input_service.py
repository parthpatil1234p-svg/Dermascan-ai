import numpy as np

from app.core.config import Settings
from app.core.model_input_config import ModelInputContract, get_model_input_contract
from app.utils.image_normalization import prepare_inference_tensor


def build_inference_tensor(
    rgb_image: np.ndarray,
    settings: Settings,
) -> tuple[np.ndarray, ModelInputContract]:
    contract = get_model_input_contract(settings)
    return prepare_inference_tensor(rgb_image, contract), contract
