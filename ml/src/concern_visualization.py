from pathlib import Path
from typing import Any

import numpy as np


def binary_curve_points(
    labels: np.ndarray, scores: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None:
    labels = np.asarray(labels, dtype=np.int8)
    scores = np.asarray(scores, dtype=np.float64)
    positive_count = int((labels == 1).sum())
    negative_count = int((labels == 0).sum())
    if positive_count == 0 or negative_count == 0:
        return None
    order = np.argsort(scores, kind="stable")[::-1]
    sorted_labels = labels[order]
    true_positives = np.cumsum(sorted_labels == 1)
    false_positives = np.cumsum(sorted_labels == 0)
    recall = true_positives / positive_count
    precision = true_positives / np.maximum(1, true_positives + false_positives)
    false_positive_rate = false_positives / negative_count
    return (
        np.r_[0.0, recall],
        np.r_[1.0, precision],
        np.r_[0.0, false_positive_rate, 1.0],
        np.r_[0.0, recall, 1.0],
    )


def save_concern_evaluation_plots(
    output: Path,
    targets: np.ndarray,
    mask: np.ndarray,
    scores: np.ndarray,
    metrics: dict[str, Any],
    labels: tuple[str, ...],
) -> None:
    import matplotlib.pyplot as plt

    plots = output / "concern_plots"
    plots.mkdir(parents=True, exist_ok=True)
    for index, label in enumerate(labels):
        selected = mask[:, index].astype(bool)
        actual = targets[selected, index]
        values = scores[selected, index]
        figure, axes = plt.subplots(2, 2, figsize=(11, 9))
        axes[0, 0].hist(values[actual == 0], bins=10, range=(0, 1), alpha=0.7, label="not observed")
        axes[0, 0].hist(values[actual == 1], bins=10, range=(0, 1), alpha=0.7, label="observed")
        axes[0, 0].axvline(metrics["per_label"][label]["threshold"], color="black", linestyle="--")
        axes[0, 0].set_title(f"{label} confidence")
        axes[0, 0].legend()
        matrix = np.asarray(metrics["per_label"][label]["confusion_matrix"])
        axes[0, 1].imshow(matrix, cmap="Blues")
        axes[0, 1].set_xticks([0, 1], ["negative", "positive"])
        axes[0, 1].set_yticks([0, 1], ["negative", "positive"])
        axes[0, 1].set_title("Confusion matrix")
        for row in range(2):
            for column in range(2):
                axes[0, 1].text(column, row, int(matrix[row, column]), ha="center", va="center")
        curves = binary_curve_points(actual, values)
        if curves is None:
            axes[1, 0].text(0.5, 0.5, "PR curve unavailable", ha="center")
            axes[1, 1].text(0.5, 0.5, "ROC curve unavailable", ha="center")
        else:
            recall, precision, false_positive_rate, true_positive_rate = curves
            axes[1, 0].plot(recall, precision, color="#0f766e")
            axes[1, 0].set(xlim=(0, 1), ylim=(0, 1), xlabel="Recall", ylabel="Precision")
            axes[1, 1].plot(false_positive_rate, true_positive_rate, color="#0369a1")
            axes[1, 1].plot([0, 1], [0, 1], color="#64748b", linestyle="--")
            axes[1, 1].set(xlim=(0, 1), ylim=(0, 1), xlabel="False positive rate", ylabel="True positive rate")
        axes[1, 0].set_title("Precision-recall curve")
        axes[1, 1].set_title("ROC curve")
        figure.tight_layout()
        figure.savefig(plots / f"{label}.png", dpi=150)
        plt.close(figure)
