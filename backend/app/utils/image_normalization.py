import numpy as np

from app.core.model_input_config import ModelInputContract


class ModelInputValidationError(Exception):
    pass


def validate_model_image(
    image: np.ndarray,
    contract: ModelInputContract,
) -> None:
    expected_shape = (contract.height, contract.width, contract.channels)
    if image.shape != expected_shape:
        raise ModelInputValidationError("Image shape does not match the model contract.")
    if image.dtype != np.uint8:
        raise ModelInputValidationError("Stored model image must use 8-bit pixels.")
    if not np.isfinite(image).all():
        raise ModelInputValidationError("Image contains invalid pixel values.")
    if int(image.min()) == int(image.max()):
        raise ModelInputValidationError("Image output has no visible variation.")
    if float(image.var()) <= 0:
        raise ModelInputValidationError("Image output is empty.")


def prepare_inference_tensor(
    image: np.ndarray,
    contract: ModelInputContract,
) -> np.ndarray:
    validate_model_image(image, contract)
    if contract.normalization != "zero_to_one":
        raise ModelInputValidationError("Unsupported normalization contract.")
    tensor = image.astype(np.float32) / 255.0
    tensor = np.expand_dims(tensor, axis=0)
    expected_shape = (1, contract.height, contract.width, contract.channels)
    if tensor.shape != expected_shape or tensor.dtype != np.float32:
        raise ModelInputValidationError("Tensor does not match the model contract.")
    if not np.isfinite(tensor).all():
        raise ModelInputValidationError("Tensor contains invalid values.")
    if float(tensor.min()) < 0.0 or float(tensor.max()) > 1.0:
        raise ModelInputValidationError("Tensor values are outside the expected range.")
    return tensor
