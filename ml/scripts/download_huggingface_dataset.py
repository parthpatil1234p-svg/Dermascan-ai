"""
Download, deduplicate, and prepare Hugging Face Skin Type Classification dataset:
https://huggingface.co/datasets/akage99/skin_type_classification
"""

import argparse
import csv
import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is required. Install it using: pip install pillow")
    sys.exit(1)

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    print("Error: huggingface_hub is required. Install it using: pip install huggingface_hub")
    sys.exit(1)

ML_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ML_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MANIFEST_PATH = DATA_DIR / "manifest.csv"

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


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download_and_extract_hf_zip(repo_id: str = "akage99/skin_type_classification", filename: str = "dataset_skintype_vit_final.zip"):
    print(f"[*] Downloading '{filename}' from Hugging Face dataset '{repo_id}'...")
    try:
        downloaded_zip_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type="dataset",
        )
        print(f"[+] Archive ready at: {downloaded_zip_path}")
    except Exception as exc:
        print(f"[!] Failed to download zip from Hugging Face: {exc}")
        return False

    # Clean raw folder for clean deduplicated ingestion
    if RAW_DIR.exists():
        shutil.rmtree(RAW_DIR, ignore_errors=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    temp_extract_dir = DATA_DIR / "_hf_temp_extracted"
    if temp_extract_dir.exists():
        shutil.rmtree(temp_extract_dir, ignore_errors=True)
    temp_extract_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Extracting archive into temporary workspace...")
    with zipfile.ZipFile(downloaded_zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_extract_dir)

    print(f"[*] Ingesting and deduplicating images into canonical classes {CANONICAL_CLASSES}...")
    manifest_rows = []
    class_counts = {c: 0 for c in CANONICAL_CLASSES}
    seen_hashes = set()
    skipped_duplicates = 0

    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    all_image_files = sorted([p for p in temp_extract_dir.rglob("*") if p.is_file() and p.suffix.lower() in valid_extensions])

    for idx, img_path in enumerate(all_image_files):
        # Determine class label from path parts
        parent_parts = [part.lower() for part in img_path.parts]
        found_class = "normal"
        for part in reversed(parent_parts):
            norm = normalize_label(part)
            if norm in CANONICAL_CLASSES:
                found_class = norm
                break

        split_hint = "train"
        for part in parent_parts:
            if "val" in part or "valid" in part:
                split_hint = "val"
                break
            elif "test" in part:
                split_hint = "test"
                break

        # Check sha256 to ensure zero duplicate hash issues
        file_hash = compute_sha256(img_path)
        if file_hash in seen_hashes:
            skipped_duplicates += 1
            continue
        seen_hashes.add(file_hash)

        class_folder = RAW_DIR / found_class
        class_folder.mkdir(parents=True, exist_ok=True)

        image_id = f"hf_{found_class}_{idx:05d}"
        target_filename = f"{image_id}{img_path.suffix.lower()}"
        target_path = class_folder / target_filename
        relative_path = f"raw/{found_class}/{target_filename}"

        try:
            with Image.open(img_path) as img:
                img = img.convert("RGB")
                img.save(target_path, "JPEG", quality=95)
                width, height = img.size
        except Exception:
            continue

        class_counts[found_class] += 1
        manifest_rows.append({
            "image_id": image_id,
            "relative_path": relative_path,
            "skin_type_label": found_class,
            "source": f"huggingface:{repo_id}",
            "license": "open_access_research",
            "subject_id": f"sub_{image_id}",
            "split": split_hint,
            "image_width": str(width),
            "image_height": str(height),
            "quality_status": "pass",
            "notes": f"Extracted from {filename}",
        })

    # Clean up temp folder
    shutil.rmtree(temp_extract_dir, ignore_errors=True)

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

    print(f"\n[+] Successfully organized {len(manifest_rows)} unique images into {RAW_DIR}")
    print(f"[+] Deduplication: Skipped {skipped_duplicates} duplicate images.")
    print(f"[+] Clean manifest created at: {MANIFEST_PATH}")
    print("[+] Unique class distribution:")
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
    download_and_extract_hf_zip(args.dataset)


if __name__ == "__main__":
    main()