import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT))

from src import CLASS_NAMES
from src.calibration import expected_calibration_error
from src.metrics import classification_metrics
from src.utils import load_config, write_json


def reliability_bins(labels: np.ndarray, probabilities: np.ndarray, bins: int = 10):
    confidence = probabilities.max(axis=1)
    correct = probabilities.argmax(axis=1) == labels
    rows = []
    for lower in np.linspace(0.0, 1.0, bins, endpoint=False):
        upper = lower + 1.0 / bins
        selected = (confidence > lower) & (confidence <= upper)
        if selected.any():
            rows.append(
                {
                    "lower": float(lower),
                    "upper": float(upper),
                    "count": int(selected.sum()),
                    "mean_confidence": float(confidence[selected].mean()),
                    "accuracy": float(correct[selected].mean()),
                }
            )
    return rows


def save_evaluation_plots(
    output: Path,
    labels: np.ndarray,
    probabilities: np.ndarray,
    metrics: dict,
) -> None:
    import matplotlib.pyplot as plt

    matrix = np.asarray(metrics["confusion_matrix"])
    figure, axis = plt.subplots(figsize=(7, 6))
    image = axis.imshow(matrix, cmap="Blues")
    axis.set_xticks(range(len(CLASS_NAMES)), CLASS_NAMES, rotation=30)
    axis.set_yticks(range(len(CLASS_NAMES)), CLASS_NAMES)
    axis.set_xlabel("Predicted")
    axis.set_ylabel("Actual")
    axis.set_title("Skin type confusion matrix")
    for row in range(len(CLASS_NAMES)):
        for column in range(len(CLASS_NAMES)):
            axis.text(column, row, int(matrix[row, column]), ha="center", va="center")
    figure.colorbar(image, ax=axis)
    figure.tight_layout()
    figure.savefig(output / "confusion_matrix.png", dpi=160)
    plt.close(figure)

    confidence = probabilities.max(axis=1)
    figure, axis = plt.subplots(figsize=(7, 4))
    axis.hist(confidence, bins=10, range=(0, 1), color="#0f766e", edgecolor="white")
    axis.set_xlabel("Top prediction confidence")
    axis.set_ylabel("Image count")
    axis.set_title("Test confidence distribution")
    figure.tight_layout()
    figure.savefig(output / "confidence_histogram.png", dpi=160)
    plt.close(figure)

    calibration = reliability_bins(labels, probabilities)
    figure, axis = plt.subplots(figsize=(6, 6))
    axis.plot([0, 1], [0, 1], linestyle="--", color="#64748b")
    if calibration:
        axis.plot(
            [row["mean_confidence"] for row in calibration],
            [row["accuracy"] for row in calibration],
            marker="o",
            color="#0369a1",
        )
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.set_xlabel("Mean confidence")
    axis.set_ylabel("Observed accuracy")
    axis.set_title("Reliability diagram")
    figure.tight_layout()
    figure.savefig(output / "reliability_diagram.png", dpi=160)
    plt.close(figure)


def save_training_history_plot(output: Path) -> None:
    import matplotlib.pyplot as plt

    path = output / "training_history.csv"
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return
    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    epochs = range(1, len(rows) + 1)
    axes[0].plot(epochs, [float(row["loss"]) for row in rows], label="train")
    axes[0].plot(epochs, [float(row["val_loss"]) for row in rows], label="validation")
    axes[0].set_title("Loss")
    axes[1].plot(epochs, [float(row["accuracy"]) for row in rows], label="train")
    axes[1].plot(epochs, [float(row["val_accuracy"]) for row in rows], label="validation")
    axes[1].set_title("Accuracy")
    for axis in axes:
        axis.set_xlabel("Epoch")
        axis.legend()
    figure.tight_layout()
    figure.savefig(output / "training_history.png", dpi=160)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ML_ROOT / "configs/skin_type_training.yaml")
    parser.add_argument("--dataset-version", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    try:
        import tensorflow as tf
    except ImportError:
        print("TensorFlow is not installed. Evaluation cannot run.")
        return 1
    from scripts.train_skin_type_model import build_dataset
    from src.dataset import read_manifest, validate_dataset

    output = ML_ROOT / config["model"]["output_directory"]
    model_path = output / "best_skin_type_model.keras"
    manifest = ML_ROOT / config["dataset"]["manifest"]
    if not model_path.is_file() or not manifest.is_file():
        print("A trained model and untouched test manifest are required.")
        return 1
    all_rows = read_manifest(manifest)
    validation = validate_dataset(all_rows, ML_ROOT / "data")
    if not validation["valid"]:
        print("Dataset validation failed; evaluation was not run.")
        return 1
    rows = [row for row in all_rows if row["split"] == "test"]
    if not rows:
        print("The untouched test split is empty.")
        return 1
    input_size = (config["input"]["width"], config["input"]["height"])
    dataset = build_dataset(
        rows,
        ML_ROOT / "data",
        input_size,
        config["training"]["batch_size"],
        False,
        config["seed"],
    )
    model = tf.keras.models.load_model(model_path)
    probabilities = model.predict(dataset, verbose=0)
    labels = np.array([CLASS_NAMES.index(row["skin_type_label"]) for row in rows])
    metrics = classification_metrics(labels, probabilities)
    metrics["expected_calibration_error"] = expected_calibration_error(labels, probabilities)
    metrics["class_names"] = list(CLASS_NAMES)
    metrics["top_confidence_distribution"] = np.histogram(
        probabilities.max(axis=1), bins=10, range=(0, 1)
    )[0].tolist()
    write_json(output / "model_metrics.json", metrics)
    write_json(
        output / "classification_report.json",
        {
            label: metrics["per_class"][index]
            for index, label in enumerate(CLASS_NAMES)
        },
    )
    write_json(output / "calibration_report.json", {"bins": reliability_bins(labels, probabilities), "expected_calibration_error": metrics["expected_calibration_error"]})
    split_distribution = {
        split: dict(Counter(row["skin_type_label"] for row in all_rows if row["split"] == split))
        for split in ("train", "validation", "test")
    }
    write_json(
        output / "evaluation_report.json",
        {
            "dataset_version": args.dataset_version,
            "dataset_size": len(all_rows),
            "class_distribution": validation["class_distribution"],
            "split_strategy": "subject-level 70/15/15 with class grouping where practical",
            "split_distribution": split_distribution,
            "architecture": config["model"]["architecture"],
            "training_configuration": config["training"],
            "test_metrics": metrics,
            "known_limitations": [
                "Image labels and technical conditions may not represent real-world use.",
                "Softmax confidence is not guaranteed to be calibrated.",
            ],
            "fairness_limitations": "Coverage cannot be assessed without consented demographic and skin-tone metadata.",
        },
    )
    save_evaluation_plots(output, labels, probabilities, metrics)
    save_training_history_plot(output)
    print(f"Evaluation artifacts written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
