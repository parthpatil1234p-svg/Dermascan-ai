import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT))

from scripts.train_skin_concern_model import build_concern_dataset
from src.concern_dataset import read_concern_manifest, targets_and_mask, validate_concern_dataset
from src.concern_labels import CONCERN_DISPLAY_NAMES, CONCERN_LABELS
from src.concern_metrics import multilabel_metrics
from src.concern_visualization import save_concern_evaluation_plots
from src.utils import load_config, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ML_ROOT / "configs/skin_concern_training.yaml")
    parser.add_argument("--dataset-version", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    try:
        import tensorflow as tf
    except ImportError:
        print("TensorFlow is not installed. Evaluation cannot run.")
        return 1
    output = ML_ROOT / config["model"]["output_directory"]
    model_path = output / "best_skin_concern_model.keras"
    thresholds_path = output / "skin_concern_thresholds.json"
    manifest = ML_ROOT / config["dataset"]["manifest"]
    if not all(path.is_file() for path in (model_path, thresholds_path, manifest)):
        print("Training and validation threshold calibration must finish before test evaluation.")
        return 1
    rows_all = read_concern_manifest(manifest)
    validation = validate_concern_dataset(rows_all, ML_ROOT / "data/concern_dataset")
    if not validation["valid"]:
        print("Dataset validation failed; test evaluation was refused.")
        return 1
    rows = [row for row in rows_all if row["split"] == "test"]
    if not rows:
        print("The untouched test split is empty.")
        return 1
    threshold_payload = json.loads(thresholds_path.read_text(encoding="utf-8"))
    if threshold_payload.get("calibrated") is not True or set(threshold_payload.get("thresholds", {})) != set(CONCERN_LABELS):
        print("Validation-calibrated per-label thresholds are required.")
        return 1
    model = tf.keras.models.load_model(model_path, compile=False)
    dataset = build_concern_dataset(rows, ML_ROOT / "data/concern_dataset", config, False)
    scores = np.asarray(model.predict(dataset, verbose=0), dtype=np.float64)
    targets, mask = targets_and_mask(rows)
    metrics = multilabel_metrics(targets, mask, scores, threshold_payload["thresholds"], CONCERN_LABELS)
    metrics["threshold_source"] = threshold_payload["source"]
    write_json(output / "skin_concern_metrics.json", metrics)
    save_concern_evaluation_plots(output, targets, mask, scores, metrics, CONCERN_LABELS)
    source_summary = dict(Counter((row["source"], row["license"]) for row in rows_all))
    write_json(
        output / "skin_concern_evaluation_report.json",
        {
            "dataset_version": args.dataset_version,
            "dataset_size": len(rows_all),
            "source_and_license_summary": [
                {"source": source, "license": license_name, "count": count}
                for (source, license_name), count in source_summary.items()
            ],
            "label_definitions": CONCERN_DISPLAY_NAMES,
            "label_distribution": validation["label_distribution"],
            "split_strategy": "deterministic subject-level multi-label balancing approximation, 70/15/15",
            "architecture": config["model"]["architecture"],
            "training_configuration": config["training"],
            "per_label_thresholds": threshold_payload["thresholds"],
            "metrics": metrics,
            "calibration_limitations": "Thresholds optimize validation F1 and are not medical calibration.",
            "skin_tone_coverage_limitations": "Coverage requires representative consented metadata and must be reported from the actual dataset.",
            "annotation_limitations": "Visible-characteristic labels are subjective and unknown labels are masked.",
            "region_detection_limitations": "The global classifier does not localize concerns; region output requires separately validated geometry.",
            "deployment_rules": "Use uncertainty bands, cautious language, ownership checks, and no medical conclusions.",
        },
    )
    print(f"Untouched test evaluation written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
