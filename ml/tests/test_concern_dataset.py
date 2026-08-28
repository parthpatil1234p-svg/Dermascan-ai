import csv
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from src.concern_dataset import (
    REQUIRED_COLUMNS,
    assign_multilabel_subject_splits,
    calculate_positive_weights,
    parse_concern_value,
    read_concern_manifest,
    targets_and_mask,
    validate_concern_dataset,
)
from src.concern_labels import CONCERN_LABELS, validate_label_order


def row(image_id: str, subject: str, relative: str, *, value: str = "0"):
    result = {
        "image_id": image_id,
        "relative_path": relative,
        "subject_id": subject,
        "source": "licensed-test-source",
        "license": "test-license",
        "split": "",
        "annotation_quality": "high",
        "annotator_count": "2",
        "notes": "",
    }
    result.update({label: value for label in CONCERN_LABELS})
    return result


def test_valid_concern_labels() -> None:
    validate_label_order(list(CONCERN_LABELS))


def test_invalid_concern_label_order_rejected() -> None:
    with pytest.raises(ValueError):
        validate_label_order(list(reversed(CONCERN_LABELS)))


def test_manifest_parsing(tmp_path: Path) -> None:
    path = tmp_path / "manifest.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerow(row("one", "s1", "raw/one.png"))
    assert read_concern_manifest(path)[0]["subject_id"] == "s1"


def test_unknown_label_masking() -> None:
    example = row("one", "s1", "raw/one.png")
    example[CONCERN_LABELS[0]] = "null"
    targets, mask = targets_and_mask([example])
    assert targets[0, 0] == 0 and mask[0, 0] == 0


def test_invalid_label_value_rejected() -> None:
    with pytest.raises(ValueError):
        parse_concern_value("maybe")


def test_duplicate_hash_detection(tmp_path: Path) -> None:
    data = tmp_path / "data"
    (data / "raw").mkdir(parents=True)
    image = Image.new("RGB", (320, 320), (100, 120, 140))
    image.save(data / "raw/a.png")
    image.save(data / "raw/b.png")
    rows = [row("a", "s1", "raw/a.png"), row("b", "s2", "raw/b.png")]
    assert any(error["code"] == "DUPLICATE_HASH" for error in validate_concern_dataset(rows, data)["errors"])


def test_duplicate_image_id_detection(tmp_path: Path) -> None:
    data = tmp_path / "data"
    (data / "raw").mkdir(parents=True)
    Image.new("RGB", (320, 320), "white").save(data / "raw/a.png")
    Image.new("RGB", (320, 320), "black").save(data / "raw/b.png")
    rows = [row("same", "s1", "raw/a.png"), row("same", "s2", "raw/b.png")]
    result = validate_concern_dataset(rows, data)
    assert any(error["code"] == "DUPLICATE_IMAGE_ID" for error in result["errors"])


def test_subject_split_isolation_and_reproducibility() -> None:
    rows = []
    for index in range(24):
        item = row(str(index), f"s{index // 2}", f"raw/{index}.png")
        item[CONCERN_LABELS[index % len(CONCERN_LABELS)]] = "1"
        rows.append(item)
    first = assign_multilabel_subject_splits(rows, seed=42, train_ratio=0.7, validation_ratio=0.15)
    second = assign_multilabel_subject_splits(rows, seed=42, train_ratio=0.7, validation_ratio=0.15)
    assert [item["split"] for item in first] == [item["split"] for item in second]
    for subject in {item["subject_id"] for item in first}:
        assert len({item["split"] for item in first if item["subject_id"] == subject}) == 1


def test_positive_class_weights() -> None:
    targets = np.array([[1, 0], [0, 0], [0, 1]], dtype=np.float32)
    mask = np.ones_like(targets)
    assert calculate_positive_weights(targets, mask).tolist() == [2.0, 2.0]
