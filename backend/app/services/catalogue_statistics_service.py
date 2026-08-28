from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import Settings


async def catalogue_statistics(collection: Any, settings: Settings) -> dict[str, Any]:
    now = datetime.now(timezone.utc)

    async def grouped(field: str) -> dict[str, int]:
        rows = await collection.aggregate(
            [
                {"$match": {"is_active": True}},
                {"$unwind": {"path": f"${field}", "preserveNullAndEmptyArrays": True}},
                {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
            ]
        ).to_list(length=None)
        return {str(row["_id"]): row["count"] for row in rows if row["_id"] is not None}

    return {
        "total_active_products": await collection.count_documents({"is_active": True}),
        "products_by_category": await grouped("category"),
        "products_by_brand": await grouped("brand_name"),
        "products_by_skin_type": await grouped("suitable_skin_types"),
        "products_by_visible_concern": await grouped("target_visible_concerns"),
        "products_by_country": await grouped("country_codes"),
        "missing_ingredient_data": await collection.count_documents(
            {"is_active": True, "normalized_ingredients": {"$size": 0}}
        ),
        "stale_pricing": await collection.count_documents(
            {
                "is_active": True,
                "price_checked_at": {
                    "$lt": now - timedelta(days=settings.product_price_stale_days)
                },
            }
        ),
        "unknown_availability": await collection.count_documents(
            {"is_active": True, "availability_status": "unknown"}
        ),
        "demo_products": await collection.count_documents(
            {"is_active": True, "is_demo_product": True}
        ),
        "verified_products": await collection.count_documents(
            {"is_active": True, "data_type": {"$in": ["verified_real", "verified_manual"]}}
        ),
    }
