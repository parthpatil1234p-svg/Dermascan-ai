from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings
from app.database.mongodb import mongo_connection
from app.models.brand import build_brand_document
from app.models.ingredient import build_ingredient_document
from app.schemas.brand import BrandCreate
from app.schemas.ingredient import IngredientCreate
from app.services.product_import_service import import_product_file

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


def _records(relative_path: str) -> list[dict]:
    payload = json.loads((DATA_ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise RuntimeError(f"Demo data file must contain a list: {relative_path}")
    return payload


async def seed_demo_data() -> dict[str, int]:
    settings = get_settings()
    database = await mongo_connection.connect(settings)
    try:
        now = datetime.now(timezone.utc)
        brand_records = _records("brands/demo_brands.json")
        for record in brand_records:
            payload = BrandCreate.model_validate(record)
            document = build_brand_document(payload, now)
            existing = await database["brands"].find_one({"brand_id": payload.brand_id})
            if existing:
                document["created_at"] = existing["created_at"]
            await database["brands"].replace_one(
                {"brand_id": payload.brand_id}, document, upsert=True
            )

        ingredient_records = _records("ingredients/base_ingredients.json")
        for record in ingredient_records:
            payload = IngredientCreate.model_validate(record)
            document = build_ingredient_document(payload, now)
            existing = await database["ingredients"].find_one(
                {"ingredient_id": payload.ingredient_id}
            )
            if existing:
                document["created_at"] = existing["created_at"]
            await database["ingredients"].replace_one(
                {"ingredient_id": payload.ingredient_id}, document, upsert=True
            )

        product_result = await import_product_file(
            DATA_ROOT / "products/demo_products.json",
            database["products"],
            database["product_import_jobs"],
            dry_run=False,
        )
        return {
            "brands": len(brand_records),
            "ingredients": len(ingredient_records),
            "products_processed": product_result.total_records,
        }
    finally:
        await mongo_connection.close()


def main() -> None:
    summary = asyncio.run(seed_demo_data())
    print(json.dumps({"status": "complete", **summary}, indent=2))


if __name__ == "__main__":
    main()
