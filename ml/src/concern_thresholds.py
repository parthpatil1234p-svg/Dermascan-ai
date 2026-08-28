from typing import Any

import numpy as np


def binary_f1(labels: np.ndarray, predictions: np.ndarray) -> float:
    true_positive = int(((labels == 1) & (predictions == 1)).sum())
    false_positive = int(((labels == 0) & (predictions == 1)).sum())
    false_negative = int(((labels == 1) & (predictions == 0)).sum())
    return 2 * true_positive / max(1, 2 * true_positive + false_positive + false_negative)


def tune_per_label_thresholds(
    targets: np.ndarray,
    mask: np.ndarray,
    scores: np.ndarray,
    labels: tuple[str, ...],
    *,
    minimum: float = 0.20,
    maximum: float = 0.80,
    step: float = 0.01,
) -> tuple[dict[str, float], dict[str, Any]]:
    thresholds: dict[str, float] = {}
    comparisons: dict[str, Any] = {}
    candidates = np.arange(minimum, maximum + step / 2, step)
    for index, label in enumerate(labels):
        selected = mask[:, index].astype(bool)
        if not selected.any() or len(np.unique(targets[selected, index])) < 2:
            raise ValueError(f"Label {label} requires known positive and negative validation examples.")
        values = [
            (float(threshold), binary_f1(targets[selected, index], scores[selected, index] >= threshold))
            for threshold in candidates
        ]
        best_threshold, best_f1 = max(values, key=lambda item: (item[1], -abs(item[0] - 0.5)))
        thresholds[label] = round(best_threshold, 4)
        comparisons[label] = {"selected_threshold": round(best_threshold, 4), "validation_f1": best_f1}
    return thresholds, comparisons


def apply_per_label_thresholds(
    scores: np.ndarray, thresholds: dict[str, float], labels: tuple[str, ...]
) -> np.ndarray:
    return np.asarray(
        [scores[index] >= thresholds[label] for index, label in enumerate(labels)],
        dtype=np.int8,
    )
