import argparse
import json
import shutil
import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ML_ROOT.parent
sys.path.insert(0, str(ML_ROOT))

from scripts.generate_model_metadata import generate_metadata
from src.utils import load_config, write_json


REQUIRED_EVALUATION_FIELDS = {
    "accuracy",
    "macro_precision",
    "macro_recall",
    "macro_f1",
    "weighted_f1",
    "cross_entropy_loss",
    "per_class",
    "confusion_matrix",
    "expected_calibration_error",
}


def validate_export_metrics(metrics: object) -> bool:
    if not isinstance(metrics, dict) or not REQUIRED_EVALUATION_FIELDS.issubset(metrics):
        return False
    if not isinstance(metrics.get("per_class"), list) or len(metrics["per_class"]) != 4:
        return False
    matrix = metrics.get("confusion_matrix")
    return isinstance(matrix, list) and len(matrix) == 4 and all(
        isinstance(row, list) and len(row) == 4 for row in matrix
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ML_ROOT / "configs/skin_type_training.yaml")
    parser.add_argument("--dataset-version", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    artifacts = ML_ROOT / config["model"]["output_directory"]
    source_model = artifacts / "best_skin_type_model.keras"
    metrics_path = artifacts / "model_metrics.json"
    if not source_model.is_file() or not metrics_path.is_file():
        print("Training and real test evaluation must finish before export.")
        return 1
    with metrics_path.open("r", encoding="utf-8") as handle:
        metrics = json.load(handle)
    if not validate_export_metrics(metrics):
        print("Evaluation metrics are incomplete; model export was refused.")
        return 1
    destination = PROJECT_ROOT / "backend/app/ml/models"
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_model, destination / "skin_type_model.keras")
    shutil.copy2(ML_ROOT / "configs/class_map.json", destination / "class_map.json")
    write_json(destination / "skin_type_model_metadata.json", generate_metadata(config, metrics, args.dataset_version))
    shutil.copy2(metrics_path, destination / "model_metrics.json")
    print(f"Exported validated artifacts to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
