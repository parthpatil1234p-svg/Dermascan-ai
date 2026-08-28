import argparse
import sys
from pathlib import Path

import numpy as np

ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT))

from scripts.train_skin_concern_model import build_concern_dataset
from src.concern_dataset import read_concern_manifest, targets_and_mask
from src.concern_labels import CONCERN_LABELS
from src.concern_thresholds import tune_per_label_thresholds
from src.utils import load_config, write_json


def build_threshold_payload(thresholds: dict[str, float]) -> dict[str, object]:
    if set(thresholds) != set(CONCERN_LABELS):
        raise ValueError("Every controlled concern label requires a threshold.")
    return {
        "source": "validation_f1_tuning",
        "calibrated": True,
        "thresholds": thresholds,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ML_ROOT / "configs/skin_concern_training.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    try:
        import tensorflow as tf
    except ImportError:
        print("TensorFlow is not installed. Threshold calibration cannot run.")
        return 1
    output = ML_ROOT / config["model"]["output_directory"]
    model_path = output / "best_skin_concern_model.keras"
    manifest = ML_ROOT / config["dataset"]["manifest"]
    if not model_path.is_file() or not manifest.is_file():
        print("A trained model and validation split are required.")
        return 1
    rows = [row for row in read_concern_manifest(manifest) if row["split"] == "validation"]
    if not rows:
        print("Validation split is empty.")
        return 1
    dataset = build_concern_dataset(rows, ML_ROOT / "data/concern_dataset", config, False)
    model = tf.keras.models.load_model(model_path, compile=False)
    scores = np.asarray(model.predict(dataset, verbose=0), dtype=np.float64)
    targets, mask = targets_and_mask(rows)
    thresholds, comparison = tune_per_label_thresholds(
        targets,
        mask,
        scores,
        CONCERN_LABELS,
        minimum=config["thresholds"]["search_min"],
        maximum=config["thresholds"]["search_max"],
        step=config["thresholds"]["search_step"],
    )
    write_json(
        output / "skin_concern_thresholds.json",
        build_threshold_payload(thresholds),
    )
    write_json(output / "threshold_comparison.json", comparison)
    print(f"Validation-derived thresholds written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
