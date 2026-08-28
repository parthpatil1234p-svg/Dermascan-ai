import numpy as np

from src.concern_metrics import multilabel_metrics
from src.concern_regions import NormalizedRegionBox, create_region_mask
from src.concern_visualization import binary_curve_points


def test_multilabel_metric_calculation() -> None:
    targets = np.array([[1, 0], [0, 1]], dtype=np.float32)
    mask = np.ones_like(targets)
    scores = np.array([[0.9, 0.1], [0.1, 0.9]])
    metrics = multilabel_metrics(targets, mask, scores, {"a": 0.5, "b": 0.5}, ("a", "b"))
    assert metrics["macro_f1"] == 1.0
    assert metrics["micro_f1"] == 1.0
    assert metrics["hamming_loss"] == 0.0


def test_region_mask_clamps_boundaries() -> None:
    mask = create_region_mask(100, 80, NormalizedRegionBox(-1, -1, 2, 2))
    assert mask is not None and mask.shape == (80, 100) and int(mask.sum()) == 8000


def test_invalid_small_region_is_skipped() -> None:
    assert create_region_mask(100, 100, NormalizedRegionBox(0, 0, 0.01, 0.01)) is None


def test_precision_recall_and_roc_curve_points() -> None:
    curves = binary_curve_points(
        np.asarray([0, 1, 0, 1]),
        np.asarray([0.1, 0.9, 0.2, 0.8]),
    )
    assert curves is not None
    recall, precision, false_positive_rate, true_positive_rate = curves
    assert recall[0] == 0 and precision[0] == 1
    assert false_positive_rate[0] == 0 and false_positive_rate[-1] == 1
    assert true_positive_rate[0] == 0 and true_positive_rate[-1] == 1
