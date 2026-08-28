import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings
from app.database.mongodb import mongo_connection
from app.models.ingredient import build_ingredient_document
from app.schemas.ingredient import IngredientCreate


async def seed() -> None:
    path = Path(__file__).resolve().parents[2] / "data" / "ingredients" / "base_ingredients.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    database = await mongo_connection.connect(get_settings())
    now = datetime.now(timezone.utc)
    for record in records:
        payload = IngredientCreate.model_validate(record)
        document = build_ingredient_document(payload, now)
        existing = await database["ingredients"].find_one({"ingredient_id": payload.ingredient_id})
        if existing:
            document["created_at"] = existing["created_at"]
        await database["ingredients"].replace_one(
            {"ingredient_id": payload.ingredient_id}, document, upsert=True
        )
    await mongo_connection.close()
    print(f"Seeded {len(records)} controlled ingredient records.")


if __name__ == "__main__":
    asyncio.run(seed())
