from typing import Any

import numpy as np


def confusion_matrix(labels: np.ndarray, predictions: np.ndarray, classes: int) -> np.ndarray:
    matrix = np.zeros((classes, classes), dtype=np.int64)
    for actual, predicted in zip(labels, predictions, strict=True):
        matrix[int(actual), int(predicted)] += 1
    return matrix


def classification_metrics(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, Any]:
    predictions = probabilities.argmax(axis=1)
    classes = probabilities.shape[1]
    matrix = confusion_matrix(labels, predictions, classes)
    per_class = []
    supports = matrix.sum(axis=1)
    for index in range(classes):
        true_positive = matrix[index, index]
        precision = true_positive / max(1, matrix[:, index].sum())
        recall = true_positive / max(1, supports[index])
        f1 = 2 * precision * recall / max(1e-12, precision + recall)
        per_class.append({"precision": precision, "recall": recall, "f1": f1, "support": int(supports[index])})
    macro_f1 = float(np.mean([item["f1"] for item in per_class]))
    weighted_f1 = float(sum(item["f1"] * item["support"] for item in per_class) / max(1, supports.sum()))
    clipped = np.clip(probabilities[np.arange(len(labels)), labels.astype(int)], 1e-7, 1.0)
    return {
        "accuracy": float((predictions == labels).mean()),
        "macro_precision": float(np.mean([item["precision"] for item in per_class])),
        "macro_recall": float(np.mean([item["recall"] for item in per_class])),
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "cross_entropy_loss": float(-np.log(clipped).mean()),
        "per_class": per_class,
        "confusion_matrix": matrix.tolist(),
    }
