import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.models.product import build_product_document
from app.models.product_import import build_import_job
from app.schemas.product import ProductCreate, ProductImportResponse
from app.services.product_validation_service import detect_duplicate_rows


class ProductImportFormatError(Exception):
    pass


LIST_FIELDS = {
    "suitable_skin_types",
    "target_visible_concerns",
    "compatibility_notes",
    "normalized_ingredients",
    "highlighted_ingredients",
    "potential_irritant_flags",
    "allergen_flags",
    "country_codes",
}
JSON_FIELDS = {"ingredients", "price", "package_size", "price_per_unit", "rating"}


def parse_import_content(content: bytes, source_type: str) -> list[dict[str, Any]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ProductImportFormatError("Import file must be UTF-8 text.") from exc
    try:
        if source_type == "json":
            data = json.loads(text)
            if not isinstance(data, list):
                raise ProductImportFormatError("JSON import must contain a list of products.")
            return data
        if source_type == "csv":
            rows = list(csv.DictReader(io.StringIO(text)))
            for row in rows:
                for field in LIST_FIELDS:
                    if field in row:
                        row[field] = [
                            item.strip() for item in row[field].split("|") if item.strip()
                        ]
                for field in JSON_FIELDS:
                    if row.get(field):
                        row[field] = json.loads(row[field])
                for field in ("is_demo_product", "is_active"):
                    if field in row:
                        row[field] = row[field].strip().lower() in {"1", "true", "yes"}
            return rows
    except (json.JSONDecodeError, csv.Error) as exc:
        raise ProductImportFormatError("The import file is not valid JSON or CSV.") from exc
    raise ProductImportFormatError("Only JSON and CSV imports are supported.")


async def import_product_records(
    records: list[dict[str, Any]],
    source_filename: str,
    source_type: str,
    products_collection: Any,
    jobs_collection: Any,
    *,
    dry_run: bool,
) -> ProductImportResponse:
    now = datetime.now(timezone.utc)
    job = build_import_job(Path(source_filename).name, source_type, now)
    job["total_records"] = len(records)
    validated: list[dict[str, Any]] = []
    errors: list[str] = []
    for row_number, record in enumerate(records, 1):
        try:
            payload = ProductCreate.model_validate(record)
            validated.append(build_product_document(payload, now))
        except ValidationError as exc:
            first = exc.errors(include_url=False)[0]
            errors.append(f"Row {row_number}: {first['msg']}")
    duplicate_indexes = detect_duplicate_rows(validated)
    valid_documents = [doc for index, doc in enumerate(validated) if index not in duplicate_indexes]
    inserted = 0
    updated = 0
    database_duplicates = 0
    if not dry_run:
        for document in valid_documents:
            existing = await products_collection.find_one({"product_id": document["product_id"]})
            if existing:
                document["created_at"] = existing["created_at"]
                await products_collection.replace_one(
                    {"product_id": document["product_id"]}, document
                )
                updated += 1
                continue
            duplicate = await products_collection.find_one(
                {
                    "normalized_product_name": document["normalized_product_name"],
                    "normalized_brand_name": document["normalized_brand_name"],
                    "category": document["category"],
                    "package_size": document.get("package_size"),
                }
            )
            if duplicate:
                database_duplicates += 1
                continue
            await products_collection.insert_one(document)
            inserted += 1
    duplicate_count = len(duplicate_indexes) + database_duplicates
    invalid_count = len(records) - len(validated)
    status = (
        "preview_ready"
        if dry_run
        else ("completed_with_errors" if invalid_count or duplicate_count else "completed")
    )
    job.update(
        {
            "status": status,
            "valid_records": len(valid_documents) - database_duplicates,
            "invalid_records": invalid_count,
            "duplicate_records": duplicate_count,
            "inserted_records": inserted,
            "updated_records": updated,
            "errors": errors[:100],
            "completed_at": datetime.now(timezone.utc),
        }
    )
    await jobs_collection.insert_one(job.copy())
    return ProductImportResponse(**{key: job[key] for key in ProductImportResponse.model_fields})


async def import_product_file(
    path: Path, products_collection: Any, jobs_collection: Any, *, dry_run: bool
) -> ProductImportResponse:
    source_type = path.suffix.lower().lstrip(".")
    return await import_product_records(
        parse_import_content(path.read_bytes(), source_type),
        path.name,
        source_type,
        products_collection,
        jobs_collection,
        dry_run=dry_run,
    )
