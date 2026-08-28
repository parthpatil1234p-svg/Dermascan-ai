import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings
from app.database.mongodb import mongo_connection
from app.models.brand import build_brand_document
from app.schemas.brand import BrandCreate


async def seed() -> None:
    path = Path(__file__).resolve().parents[2] / "data" / "brands" / "demo_brands.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    database = await mongo_connection.connect(get_settings())
    now = datetime.now(timezone.utc)
    for record in records:
        payload = BrandCreate.model_validate(record)
        document = build_brand_document(payload, now)
        existing = await database["brands"].find_one({"brand_id": payload.brand_id})
        if existing:
            document["created_at"] = existing["created_at"]
        await database["brands"].replace_one({"brand_id": payload.brand_id}, document, upsert=True)
    await mongo_connection.close()
    print(f"Seeded {len(records)} fictional demonstration brands.")


if __name__ == "__main__":
    asyncio.run(seed())
