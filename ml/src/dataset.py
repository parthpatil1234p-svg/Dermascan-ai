import csv
import hashlib
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, UnidentifiedImageError

from src import CLASS_NAMES

REQUIRED_COLUMNS = (
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
)


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Manifest is missing columns: {', '.join(missing)}")
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def perceptual_hash(path: Path) -> int:
    with Image.open(path) as image:
        values = np.asarray(image.convert("L").resize((8, 8)), dtype=np.float32)
    bits = values >= float(values.mean())
    return sum(int(value) << index for index, value in enumerate(bits.flat))


def validate_dataset(rows: list[dict[str, str]], data_root: Path) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    hashes: dict[str, str] = {}
    perceptual: list[tuple[str, int]] = []
    seen_paths: set[str] = set()
    sizes: list[tuple[int, int]] = []
    distribution: Counter[str] = Counter()
    subject_splits: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        image_id = row.get("image_id", "")
        label = row.get("skin_type_label", "").lower()
        relative_path = row.get("relative_path", "")
        if label not in CLASS_NAMES:
            errors.append({"image_id": image_id, "code": "INVALID_CLASS"})
        else:
            distribution[label] += 1
        if not row.get("source") or not row.get("license"):
            errors.append({"image_id": image_id, "code": "MISSING_SOURCE_OR_LICENSE"})
        if relative_path in seen_paths:
            errors.append({"image_id": image_id, "code": "DUPLICATE_PATH"})
        seen_paths.add(relative_path)
        if row.get("subject_id") and row.get("split"):
            subject_splits[row["subject_id"]].add(row["split"])

        image_path = (data_root / relative_path).resolve()
        if data_root.resolve() not in image_path.parents:
            errors.append({"image_id": image_id, "code": "UNSAFE_PATH"})
            continue
        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            errors.append({"image_id": image_id, "code": "UNSUPPORTED_FORMAT"})
            continue
        try:
            with Image.open(image_path) as image:
                image.verify()
            with Image.open(image_path) as image:
                sizes.append(image.size)
            digest = file_sha256(image_path)
            if digest in hashes:
                errors.append({"image_id": image_id, "code": "DUPLICATE_HASH"})
            else:
                hashes[digest] = image_id
            perceptual.append((image_id, perceptual_hash(image_path)))
        except (OSError, UnidentifiedImageError):
            errors.append({"image_id": image_id, "code": "UNREADABLE_IMAGE"})

    leakage = sorted(subject for subject, splits in subject_splits.items() if len(splits) > 1)
    near_duplicates: list[list[str]] = []
    for index, (left_id, left_hash) in enumerate(perceptual):
        for right_id, right_hash in perceptual[index + 1 :]:
            if (left_hash ^ right_hash).bit_count() <= 5:
                near_duplicates.append([left_id, right_id])

    return {
        "valid": not errors and not leakage,
        "row_count": len(rows),
        "class_distribution": dict(distribution),
        "image_size_min": list(map(min, zip(*sizes))) if sizes else None,
        "image_size_max": list(map(max, zip(*sizes))) if sizes else None,
        "split_leakage_subjects": leakage,
        "potential_near_duplicates": near_duplicates,
        "errors": errors,
    }


def assign_subject_splits(
    rows: list[dict[str, str]],
    *,
    seed: int,
    train_ratio: float,
    validation_ratio: float,
) -> list[dict[str, str]]:
    subjects = sorted({row["subject_id"] for row in rows if row.get("subject_id")})
    if len(subjects) != len({row.get("subject_id") for row in rows}):
        raise ValueError("Every row requires a subject_id for subject-level splitting.")
    labels_by_subject: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        labels_by_subject[row["subject_id"]][row["skin_type_label"]] += 1

    grouped_subjects: dict[str, list[str]] = defaultdict(list)
    for subject in subjects:
        counts = labels_by_subject[subject]
        most_common = counts.most_common()
        group = most_common[0][0] if len(most_common) == 1 else "mixed"
        grouped_subjects[group].append(subject)

    rng = random.Random(seed)
    assignments: dict[str, str] = {}
    for group in sorted(grouped_subjects):
        group_subjects = grouped_subjects[group]
        rng.shuffle(group_subjects)
        train_end = round(len(group_subjects) * train_ratio)
        validation_end = train_end + round(len(group_subjects) * validation_ratio)
        for index, subject in enumerate(group_subjects):
            assignments[subject] = (
                "train"
                if index < train_end
                else "validation"
                if index < validation_end
                else "test"
            )
    return [{**row, "split": assignments[row["subject_id"]]} for row in rows]
