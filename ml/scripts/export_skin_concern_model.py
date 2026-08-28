import argparse
import json
import shutil
import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ML_ROOT.parent
sys.path.insert(0, str(ML_ROOT))

from scripts.generate_concern_model_metadata import generate_concern_metadata
from src.concern_labels import CONCERN_LABELS
from src.utils import load_config, write_json


def artifacts_are_exportable(metrics: object, thresholds: object) -> bool:
    return (
        isinstance(metrics, dict)
        and isinstance(metrics.get("per_label"), dict)
        and set(metrics["per_label"]) == set(CONCERN_LABELS)
        and metrics.get("threshold_source") == "validation_f1_tuning"
        and isinstance(thresholds, dict)
        and thresholds.get("calibrated") is True
        and set(thresholds.get("thresholds", {})) == set(CONCERN_LABELS)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ML_ROOT / "configs/skin_concern_training.yaml")
    parser.add_argument("--dataset-version", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    artifacts = ML_ROOT / config["model"]["output_directory"]
    model_path = artifacts / "best_skin_concern_model.keras"
    metrics_path = artifacts / "skin_concern_metrics.json"
    thresholds_path = artifacts / "skin_concern_thresholds.json"
    if not all(path.is_file() for path in (model_path, metrics_path, thresholds_path)):
        print("Training, calibration, and real test evaluation must finish before export.")
        return 1
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    thresholds = json.loads(thresholds_path.read_text(encoding="utf-8"))
    if not artifacts_are_exportable(metrics, thresholds):
        print("Concern artifacts are incomplete or uncalibrated; export was refused.")
        return 1
    destination = PROJECT_ROOT / "backend/app/ml/models"
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(model_path, destination / "skin_concern_model.keras")
    shutil.copy2(ML_ROOT / "configs/skin_concern_label_map.json", destination / "skin_concern_label_map.json")
    shutil.copy2(thresholds_path, destination / "skin_concern_thresholds.json")
    shutil.copy2(metrics_path, destination / "skin_concern_metrics.json")
    write_json(
        destination / "skin_concern_model_metadata.json",
        generate_concern_metadata(config, metrics, thresholds["thresholds"], args.dataset_version),
    )
    print(f"Exported validated concern artifacts to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
