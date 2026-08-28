from typing import Any

import numpy as np


def _roc_auc(labels: np.ndarray, scores: np.ndarray) -> float | None:
    positives = labels == 1
    negatives = labels == 0
    if not positives.any() or not negatives.any():
        return None
    comparisons = scores[positives, None] - scores[negatives][None, :]
    return float(((comparisons > 0).sum() + 0.5 * (comparisons == 0).sum()) / comparisons.size)


def _pr_auc(labels: np.ndarray, scores: np.ndarray) -> float | None:
    positives = int((labels == 1).sum())
    if positives == 0:
        return None
    order = np.argsort(scores)[::-1]
    sorted_labels = labels[order]
    true_positives = np.cumsum(sorted_labels == 1)
    false_positives = np.cumsum(sorted_labels == 0)
    recall = true_positives / positives
    precision = true_positives / np.maximum(1, true_positives + false_positives)
    return float(np.sum((recall - np.r_[0.0, recall[:-1]]) * precision))


def multilabel_metrics(
    targets: np.ndarray,
    mask: np.ndarray,
    scores: np.ndarray,
    thresholds: dict[str, float],
    labels: tuple[str, ...],
) -> dict[str, Any]:
    predictions = np.zeros_like(targets, dtype=np.int8)
    per_label: dict[str, Any] = {}
    totals = np.zeros(4, dtype=np.int64)
    weighted_f1_numerator = 0.0
    total_support = 0

    for index, label in enumerate(labels):
        selected = mask[:, index].astype(bool)
        actual = targets[selected, index].astype(np.int8)
        concern_scores = scores[selected, index]
        predicted = (concern_scores >= thresholds[label]).astype(np.int8)
        predictions[selected, index] = predicted
        true_positive = int(((actual == 1) & (predicted == 1)).sum())
        true_negative = int(((actual == 0) & (predicted == 0)).sum())
        false_positive = int(((actual == 0) & (predicted == 1)).sum())
        false_negative = int(((actual == 1) & (predicted == 0)).sum())
        precision = true_positive / max(1, true_positive + false_positive)
        recall = true_positive / max(1, true_positive + false_negative)
        specificity = true_negative / max(1, true_negative + false_positive)
        f1 = 2 * precision * recall / max(1e-12, precision + recall)
        support = int((actual == 1).sum())
        totals += np.asarray([true_positive, true_negative, false_positive, false_negative])
        weighted_f1_numerator += f1 * support
        total_support += support
        per_label[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "specificity": specificity,
            "support": support,
            "known_count": int(selected.sum()),
            "roc_auc": _roc_auc(actual, concern_scores),
            "pr_auc": _pr_auc(actual, concern_scores),
            "threshold": thresholds[label],
            "confusion_matrix": [[true_negative, false_positive], [false_negative, true_positive]],
        }

    tp, tn, fp, fn = map(int, totals)
    micro_precision = tp / max(1, tp + fp)
    micro_recall = tp / max(1, tp + fn)
    micro_f1 = 2 * micro_precision * micro_recall / max(1e-12, micro_precision + micro_recall)
    known = mask.astype(bool)
    hamming = float((predictions[known] != targets[known]).mean()) if known.any() else 0.0
    fully_known = known.all(axis=1)
    subset_accuracy = (
        float((predictions[fully_known] == targets[fully_known]).all(axis=1).mean())
        if fully_known.any()
        else None
    )
    ranking_scores = []
    for row in range(len(targets)):
        positive_indexes = np.flatnonzero((targets[row] == 1) & known[row])
        known_indexes = np.flatnonzero(known[row])
        if not len(positive_indexes):
            continue
        precisions = []
        for positive in positive_indexes:
            ranked = known_indexes[scores[row, known_indexes] >= scores[row, positive]]
            precisions.append(float(targets[row, ranked].sum() / max(1, len(ranked))))
        ranking_scores.append(float(np.mean(precisions)))

    f1_values = [item["f1"] for item in per_label.values()]
    return {
        "per_label": per_label,
        "macro_f1": float(np.mean(f1_values)),
        "micro_f1": micro_f1,
        "weighted_f1": weighted_f1_numerator / max(1, total_support),
        "hamming_loss": hamming,
        "label_ranking_average_precision": float(np.mean(ranking_scores)) if ranking_scores else None,
        "subset_accuracy": subset_accuracy,
    }
