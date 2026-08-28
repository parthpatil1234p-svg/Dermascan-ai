import numpy as np

from app.services.skin_concern_region_service import (
    region_names_for_global_prediction,
    validate_region_geometry,
)
from app.utils.facial_regions import NormalizedRegionBox, create_safe_region_mask


def test_missing_geometry_uses_honest_full_face_fallback() -> None:
    context = validate_region_geometry(np.zeros((224, 224, 3), dtype=np.uint8), None)
    assert context.precise_regions_available is False
    assert context.issue_code == "REGION_INFORMATION_UNAVAILABLE"
    assert region_names_for_global_prediction(context) == ["Full Face"]


def test_valid_region_geometry_is_clamped_and_safe() -> None:
    box = NormalizedRegionBox(-0.1, 0.1, 0.6, 0.8)
    mask = create_safe_region_mask(100, 80, box)
    assert mask is not None
    assert mask.shape == (80, 100)
    assert mask.any()


def test_invalid_region_geometry_is_rejected() -> None:
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    box = NormalizedRegionBox(0.8, 0.8, 0.2, 0.2)
    context = validate_region_geometry(image, {"nose": box})
    assert context.precise_regions_available is False


def test_unknown_region_name_is_not_accepted() -> None:
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    box = NormalizedRegionBox(0.1, 0.1, 0.5, 0.5)
    context = validate_region_geometry(image, {"diagnostic_zone": box})
    assert context.available_regions == ("full_face",)
