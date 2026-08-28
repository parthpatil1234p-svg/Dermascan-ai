import argparse
import csv
import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT))

from src.dataset import (
    REQUIRED_COLUMNS,
    assign_subject_splits,
    read_manifest,
    validate_dataset,
)
from src.utils import load_config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ML_ROOT / "configs/skin_type_training.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    manifest = ML_ROOT / config["dataset"]["manifest"]
    if not manifest.is_file():
        print(f"Dataset manifest not found: {manifest}")
        return 1
    manifest_rows = read_manifest(manifest)
    validation = validate_dataset(manifest_rows, ML_ROOT / "data")
    if validation["errors"]:
        print("Dataset validation errors must be resolved before splitting.")
        return 1
    rows = assign_subject_splits(
        manifest_rows,
        seed=int(config["seed"]),
        train_ratio=float(config["dataset"]["train_ratio"]),
        validation_ratio=float(config["dataset"]["validation_ratio"]),
    )
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Updated subject-level split assignments in {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
