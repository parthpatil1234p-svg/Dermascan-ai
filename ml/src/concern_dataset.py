import csv
import hashlib
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, UnidentifiedImageError

from src.concern_labels import CONCERN_LABELS

BASE_COLUMNS = (
    "image_id",
    "relative_path",
    "subject_id",
    "source",
    "license",
    "split",
)
TRAILING_COLUMNS = ("annotation_quality", "annotator_count", "notes")
REQUIRED_COLUMNS = BASE_COLUMNS + CONCERN_LABELS + TRAILING_COLUMNS
UNKNOWN_VALUES = {"", "null", "none", "unknown", "na", "n/a"}
ANNOTATION_QUALITIES = {"high", "medium", "low", "unknown"}


def read_concern_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Manifest is missing columns: {', '.join(missing)}")
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def parse_concern_value(value: str | None) -> float:
    normalized = (value or "").strip().lower()
    if normalized in UNKNOWN_VALUES:
        return np.nan
    if normalized == "0":
        return 0.0
    if normalized == "1":
        return 1.0
    raise ValueError("Concern labels must be 0, 1, or unknown.")


def targets_and_mask(rows: list[dict[str, str]]) -> tuple[np.ndarray, np.ndarray]:
    targets = np.asarray(
        [[parse_concern_value(row[label]) for label in CONCERN_LABELS] for row in rows],
        dtype=np.float32,
    )
    mask = np.isfinite(targets).astype(np.float32)
    return np.nan_to_num(targets, nan=0.0), mask


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_concern_dataset(
    rows: list[dict[str, str]], data_root: Path
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    seen_image_ids: set[str] = set()
    seen_paths: set[str] = set()
    hashes: dict[str, tuple[str, str]] = {}
    subject_splits: dict[str, set[str]] = defaultdict(set)
    distribution = {
        label: {"positive": 0, "negative": 0, "unknown": 0}
        for label in CONCERN_LABELS
    }
    split_distribution: Counter[str] = Counter()

    for row in rows:
        image_id = row.get("image_id", "")
        relative = row.get("relative_path", "")
        split = row.get("split", "")
        if not image_id or not relative or not row.get("subject_id"):
            errors.append({"image_id": image_id, "code": "MISSING_ID_PATH_OR_SUBJECT"})
        if image_id in seen_image_ids:
            errors.append({"image_id": image_id, "code": "DUPLICATE_IMAGE_ID"})
        seen_image_ids.add(image_id)
        if not row.get("source") or not row.get("license"):
            errors.append({"image_id": image_id, "code": "MISSING_SOURCE_OR_LICENSE"})
        if split and split not in {"train", "validation", "test"}:
            errors.append({"image_id": image_id, "code": "INVALID_SPLIT"})
        if split:
            split_distribution[split] += 1
            subject_splits[row.get("subject_id", "")].add(split)
        if relative in seen_paths:
            errors.append({"image_id": image_id, "code": "DUPLICATE_PATH"})
        seen_paths.add(relative)
        if row.get("annotation_quality", "").lower() not in ANNOTATION_QUALITIES:
            errors.append({"image_id": image_id, "code": "INVALID_ANNOTATION_QUALITY"})
        try:
            if int(row.get("annotator_count", "0")) < 1:
                raise ValueError
        except ValueError:
            errors.append({"image_id": image_id, "code": "INVALID_ANNOTATOR_COUNT"})

        for label in CONCERN_LABELS:
            try:
                value = parse_concern_value(row.get(label))
                key = "unknown" if np.isnan(value) else "positive" if value == 1 else "negative"
                distribution[label][key] += 1
            except ValueError:
                errors.append({"image_id": image_id, "code": f"INVALID_LABEL:{label}"})

        image_path = (data_root / relative).resolve()
        if data_root.resolve() not in image_path.parents:
            errors.append({"image_id": image_id, "code": "UNSAFE_PATH"})
            continue
        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            errors.append({"image_id": image_id, "code": "UNSUPPORTED_FORMAT"})
            continue
        try:
            with Image.open(image_path) as image:
                image.verify()
            digest = file_sha256(image_path)
            if digest in hashes:
                prior_id, prior_split = hashes[digest]
                code = "DUPLICATE_HASH_ACROSS_SPLITS" if prior_split != split else "DUPLICATE_HASH"
                errors.append({"image_id": image_id, "code": code, "duplicate_of": prior_id})
            else:
                hashes[digest] = (image_id, split)
        except (OSError, UnidentifiedImageError):
            errors.append({"image_id": image_id, "code": "UNREADABLE_IMAGE"})

    leakage = sorted(subject for subject, splits in subject_splits.items() if len(splits) > 1)
    return {
        "valid": not errors and not leakage,
        "row_count": len(rows),
        "label_distribution": distribution,
        "split_distribution": dict(split_distribution),
        "split_leakage_subjects": leakage,
        "errors": errors,
    }


def assign_multilabel_subject_splits(
    rows: list[dict[str, str]],
    *,
    seed: int,
    train_ratio: float,
    validation_ratio: float,
) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        subject = row.get("subject_id", "")
        if not subject:
            raise ValueError("Every row requires a subject_id.")
        grouped[subject].append(row)

    split_names = ("train", "validation", "test")
    ratios = np.asarray(
        [train_ratio, validation_ratio, 1.0 - train_ratio - validation_ratio]
    )
    if (ratios <= 0).any() or not np.isclose(ratios.sum(), 1.0):
        raise ValueError("Split ratios must be positive and sum to one.")

    rng = random.Random(seed)
    subjects = list(grouped)
    rng.shuffle(subjects)
    subject_vectors: dict[str, np.ndarray] = {}
    for subject in subjects:
        target, mask = targets_and_mask(grouped[subject])
        subject_vectors[subject] = ((target * mask).sum(axis=0) > 0).astype(float)
    subjects.sort(key=lambda subject: (-subject_vectors[subject].sum(), subject))

    total_labels = sum(subject_vectors.values(), np.zeros(len(CONCERN_LABELS)))
    target_labels = np.outer(ratios, total_labels)
    target_subjects = ratios * len(subjects)
    current_labels = np.zeros_like(target_labels)
    current_subjects = np.zeros(3)
    assignments: dict[str, str] = {}

    for subject in subjects:
        vector = subject_vectors[subject]
        costs = []
        for index in range(3):
            label_cost = np.square(current_labels[index] + vector - target_labels[index]).sum()
            size_cost = (current_subjects[index] + 1 - target_subjects[index]) ** 2
            costs.append(float(label_cost + size_cost))
        chosen = min(range(3), key=lambda index: (costs[index], current_subjects[index], index))
        assignments[subject] = split_names[chosen]
        current_labels[chosen] += vector
        current_subjects[chosen] += 1

    return [{**row, "split": assignments[row["subject_id"]]} for row in rows]


def calculate_positive_weights(targets: np.ndarray, mask: np.ndarray) -> np.ndarray:
    positives = (targets * mask).sum(axis=0)
    negatives = ((1.0 - targets) * mask).sum(axis=0)
    return np.where(positives > 0, np.maximum(1.0, negatives / positives), 1.0).astype(
        np.float32
    )
