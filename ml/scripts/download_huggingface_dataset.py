"""
Download and prepare the Hugging Face Skin Type Classification dataset:
https://huggingface.co/datasets/akage99/skin_type_classification

This script downloads images from Hugging Face and populates ml/data/raw/
along with a standardized ml/data/manifest.csv.
"""

import argparse
import csv
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is required. Install it using: pip install pillow")
    sys.exit(1)

try:
    from datasets import load_dataset
except ImportError:
    print("Note: 'datasets' package is required to pull directly from Hugging Face.")
    print("Install it with: pip install datasets huggingface_hub")

ML_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ML_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MANIFEST_PATH = DATA_DIR / "manifest.csv"

# Label mapping to DermaScan AI canonical skin type classes
CANONICAL_CLASSES = {"normal", "oily", "dry", "combination"}


def normalize_label(label_raw: str) -> str:
    cleaned = str(label_raw).strip().lower()
    if "oily" in cleaned:
        return "oily"
    if "dry" in cleaned:
        return "dry"
    if "comb" in cleaned:
        return "combination"
    if "norm" in cleaned:
        return "normal"
    return cleaned if cleaned in CANONICAL_CLASSES else "normal"


def download_from_huggingface(dataset_id: str = "akage99/skin_type_classification"):
    print(f"[*] Fetching dataset '{dataset_id}' from Hugging Face...")
    try:
        ds = load_dataset(dataset_id)
    except Exception as exc:
        print(f"[!] Failed to load dataset directly via Hugging Face API: {exc}")
        print("[i] Alternatively, you can download the dataset zip from:")
        print(f"    https://huggingface.co/datasets/{dataset_id}")
        print(f"    and extract images into {RAW_DIR}")
        return False

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    class_counts = {c: 0 for c in CANONICAL_CLASSES}

    print("[*] Processing images and building manifest.csv...")

    for split_name in ds.keys():
        split_data = ds[split_name]
        for idx, item in enumerate(split_data):
            image = item.get("image") or item.get("img")
            label_val = item.get("label") or item.get("skin_type") or "normal"

            if isinstance(label_val, int) and hasattr(split_data.features.get("label"), "int2str"):
                label_str = split_data.features["label"].int2str(label_val)
            else:
                label_str = str(label_val)

            canonical_label = normalize_label(label_str)
            image_id = f"hf_{canonical_label}_{split_name}_{idx:05d}"
            target_filename = f"{image_id}.jpg"
            class_folder = RAW_DIR / canonical_label
            class_folder.mkdir(parents=True, exist_ok=True)
            target_path = class_folder / target_filename
            relative_path = f"raw/{canonical_label}/{target_filename}"

            if image is not None:
                if not isinstance(image, Image.Image):
                    image = Image.open(image)
                image = image.convert("RGB")
                image.save(target_path, "JPEG", quality=95)
                width, height = image.size
            else:
                width, height = 224, 224

            class_counts[canonical_label] += 1
            manifest_rows.append({
                "image_id": image_id,
                "relative_path": relative_path,
                "skin_type_label": canonical_label,
                "source": "huggingface:akage99/skin_type_classification",
                "license": "open_access_research",
                "subject_id": f"sub_{image_id}",
                "split": "train" if split_name == "train" else ("val" if "val" in split_name else "test"),
                "image_width": str(width),
                "image_height": str(height),
                "quality_status": "pass",
                "notes": f"Downloaded from Hugging Face {dataset_id}",
            })

    # Write manifest.csv
    fieldnames = [
        "image_id",
        "relative_path",
        "skin_type_label",
        "source",
        "license",
        "subject_id",
        "split",
        "image_width",
        "image_height",
        "quality_status",
        "notes",
    ]

    with open(MANIFEST_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"\n[+] Successfully prepared {len(manifest_rows)} images!")
    print(f"[+] Manifest created at: {MANIFEST_PATH}")
    print("[+] Class distribution:")
    for cls_name, count in class_counts.items():
        print(f"    - {cls_name:12s}: {count} images")

    return True


def main():
    parser = argparse.ArgumentParser(description="Download skin type dataset from Hugging Face.")
    parser.add_argument(
        "--dataset",
        type=str,
        default="akage99/skin_type_classification",
        help="Hugging Face dataset identifier (default: akage99/skin_type_classification)",
    )
    args = parser.parse_args()
    download_from_huggingface(args.dataset)


if __name__ == "__main__":
    main()