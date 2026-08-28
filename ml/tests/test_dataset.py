import csv
from pathlib import Path

from PIL import Image

from src.dataset import REQUIRED_COLUMNS, assign_subject_splits, read_manifest, validate_dataset


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def row(image_id: str, relative_path: str, label: str, subject: str) -> dict[str, str]:
    return {
        "image_id": image_id,
        "relative_path": relative_path,
        "skin_type_label": label,
        "source": "licensed-test-source",
        "license": "test-license",
        "subject_id": subject,
        "split": "",
        "image_width": "320",
        "image_height": "320",
        "quality_status": "passed",
        "notes": "",
    }


def test_manifest_parsing(tmp_path: Path) -> None:
    path = tmp_path / "manifest.csv"
    write_manifest(path, [row("one", "raw/one.png", "normal", "s1")])
    assert read_manifest(path)[0]["skin_type_label"] == "normal"


def test_valid_class_names(tmp_path: Path) -> None:
    data = tmp_path / "data"
    (data / "raw").mkdir(parents=True)
    rows = []
    for index, label in enumerate(("normal", "oily", "dry", "combination")):
        Image.new("RGB", (320 + index, 320), (80 + index * 20, 100, 120)).save(data / "raw" / f"{index}.png")
        rows.append(row(str(index), f"raw/{index}.png", label, f"s{index}"))
    assert not any(error["code"] == "INVALID_CLASS" for error in validate_dataset(rows, data)["errors"])


def test_invalid_class_rejected(tmp_path: Path) -> None:
    data = tmp_path / "data"
    (data / "raw").mkdir(parents=True)
    Image.new("RGB", (320, 320)).save(data / "raw/x.png")
    report = validate_dataset([row("x", "raw/x.png", "sensitive", "s1")], data)
    assert any(error["code"] == "INVALID_CLASS" for error in report["errors"])


def test_duplicate_hash_detection(tmp_path: Path) -> None:
    data = tmp_path / "data"
    (data / "raw").mkdir(parents=True)
    image = Image.new("RGB", (320, 320), (100, 110, 120))
    image.save(data / "raw/a.png")
    image.save(data / "raw/b.png")
    report = validate_dataset(
        [row("a", "raw/a.png", "normal", "s1"), row("b", "raw/b.png", "normal", "s2")], data
    )
    assert any(error["code"] == "DUPLICATE_HASH" for error in report["errors"])


def test_split_reproducibility() -> None:
    rows = [row(str(index), f"raw/{index}.png", "normal", f"s{index}") for index in range(20)]
    first = assign_subject_splits(rows, seed=42, train_ratio=0.7, validation_ratio=0.15)
    second = assign_subject_splits(rows, seed=42, train_ratio=0.7, validation_ratio=0.15)
    assert [item["split"] for item in first] == [item["split"] for item in second]


def test_subject_level_split_isolation() -> None:
    rows = [row("a", "raw/a.png", "normal", "same"), row("b", "raw/b.png", "oily", "same")]
    rows += [row(str(index), f"raw/{index}.png", "dry", f"s{index}") for index in range(8)]
    assigned = assign_subject_splits(rows, seed=3, train_ratio=0.7, validation_ratio=0.15)
    assert len({item["split"] for item in assigned if item["subject_id"] == "same"}) == 1
