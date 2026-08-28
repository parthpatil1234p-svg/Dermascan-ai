import argparse
import json
import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT))

from src.concern_dataset import read_concern_manifest, validate_concern_dataset
from src.utils import load_config, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ML_ROOT / "configs/skin_concern_training.yaml")
    parser.add_argument("--report", type=Path, default=ML_ROOT / "concern_artifacts/dataset_validation.json")
    args = parser.parse_args()
    config = load_config(args.config)
    manifest = ML_ROOT / config["dataset"]["manifest"]
    if not manifest.is_file():
        report = {"valid": False, "errors": [{"code": "MANIFEST_NOT_FOUND", "path": str(manifest)}]}
    else:
        report = validate_concern_dataset(read_concern_manifest(manifest), ML_ROOT / "data/concern_dataset")
    write_json(args.report, report)
    print(json.dumps(report, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
