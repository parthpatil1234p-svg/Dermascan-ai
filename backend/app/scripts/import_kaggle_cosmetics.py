import asyncio
import csv
import io
import json
import logging
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pymongo

from app.core.catalogue import (
    PRODUCT_CATEGORIES,
    SKIN_TYPES,
    VISIBLE_CONCERNS,
)
from app.core.config import get_settings
from app.models.product import slugify

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CATEGORY_MAP = {
    "Cleanser": "cleanser",
    "Moisturizer": "moisturizer",
    "Treatment": "serum",
    "Sun protect": "sunscreen",
    "Face Mask": "face_mask",
    "Eye cream": "under_eye_product",
}

CONCERN_RULES = [
    (re.compile(r"\b(salicylic acid|bha|tea tree|sulfur|willow bark)\b", re.I), ["acne_like_spots", "visible_pores"]),
    (re.compile(r"\b(niacinamide|zinc|zinc pca)\b", re.I), ["visible_oiliness", "visible_pores", "uneven_looking_tone"]),
    (re.compile(r"\b(hyaluronic acid|sodium hyaluronate|glycerin|panthenol|ceramide|squalane|aloe)\b", re.I), ["dry_looking_areas"]),
    (re.compile(r"\b(vitamin c|ascorbic acid|glycolic acid|aha|lactic acid|arbutin|tranexamic acid|licorice)\b", re.I), ["dark_spots", "dull_looking_appearance", "uneven_looking_tone"]),
    (re.compile(r"\b(retinol|retinal|bakuchiol|peptide|collagen|adenosine)\b", re.I), ["fine_line_visibility"]),
    (re.compile(r"\b(centella|cica|madecassoside|allantoin|oat extract|colloidal oatmeal|chamomile|feverfew)\b", re.I), ["visible_redness"]),
    (re.compile(r"\b(caffeine|coffee extract|peptide)\b", re.I), ["under_eye_darkness"]),
]


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\ufffd", "e").replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    return " ".join(text.strip().split())


def detect_concerns(ingredients_text: str, category: str) -> list[str]:
    concerns = set()
    for pattern, matched_concerns in CONCERN_RULES:
        if pattern.search(ingredients_text):
            concerns.update(matched_concerns)

    if category == "sunscreen":
        concerns.add("dark_spots")
        concerns.add("uneven_looking_tone")
    elif category == "under_eye_product":
        concerns.add("under_eye_darkness")

    return sorted(list(concerns))


def parse_ingredients(ingredients_raw: str) -> tuple[list[dict[str, Any]], list[str], list[str], str]:
    if not ingredients_raw or ingredients_raw.strip().lower() in {"unknown", "visit the la mer counter", "#name?"}:
        return (
            [{"display_name": "Purified Water", "position": 1}],
            ["water"],
            ["Water"],
            "unknown",
        )

    parts = [clean_text(p) for p in ingredients_raw.split(",") if clean_text(p)]
    if not parts:
        parts = ["Water"]

    parsed_ingredients = []
    normalized = []
    for idx, part in enumerate(parts[:50], start=1):
        name = part[:100]
        parsed_ingredients.append({"display_name": name, "position": idx})
        normalized.append(name.lower())

    highlighted = [p["display_name"] for p in parsed_ingredients[:3]]

    # Check fragrance
    full_str = " ".join(normalized)
    if "fragrance" in full_str or "parfum" in full_str:
        fragrance_status = "contains_added_fragrance"
    elif any(eo in full_str for eo in ["lavender oil", "citrus peel", "eucalyptus oil", "essential oil"]):
        fragrance_status = "contains_fragrant_ingredients"
    else:
        fragrance_status = "fragrance_free"

    return parsed_ingredients, normalized, highlighted, fragrance_status


def process_kaggle_row(row: dict[str, str], index: int) -> dict[str, Any] | None:
    raw_label = clean_text(row.get("Label") or row.get("\ufeffLabel", ""))
    category = CATEGORY_MAP.get(raw_label)
    if not category:
        return None

    brand_name = clean_text(row.get("Brand", ""))
    product_name = clean_text(row.get("Name", ""))
    if not brand_name or not product_name:
        return None

    # Suitable skin types
    skin_types = []
    if row.get("Normal") == "1":
        skin_types.append("normal")
    if row.get("Oily") == "1":
        skin_types.append("oily")
    if row.get("Dry") == "1":
        skin_types.append("dry")
    if row.get("Combination") == "1":
        skin_types.append("combination")
    if row.get("Sensitive") == "1":
        skin_types.append("sensitive_self_reported")

    if not skin_types:
        skin_types = ["all_skin_types"]

    # Price conversion: USD to approx INR with standard rounding
    try:
        usd_price = float(row.get("Price", 0))
        inr_amount = max(299, round(usd_price * 83))
    except (ValueError, TypeError):
        inr_amount = 499

    try:
        rating_val = float(row.get("Rank", 0))
    except (ValueError, TypeError):
        rating_val = 4.2

    ingredients_raw = row.get("Ingredients", "")
    parsed_ingredients, normalized, highlighted, fragrance_status = parse_ingredients(ingredients_raw)
    concerns = detect_concerns(ingredients_raw, category)

    brand_id = f"BRD-{slugify(brand_name)[:20].upper()}"
    product_id = f"PRD-KAG-{index:05d}"

    short_description = f"{product_name} by {brand_name}. A high-performance {category} formulated for {', '.join(skin_types)} skin."

    product_doc = {
        "product_id": product_id,
        "product_name": product_name[:180],
        "slug": slugify(f"{brand_name} {product_name}")[:180],
        "normalized_product_name": product_name.casefold(),
        "brand_id": brand_id,
        "brand_name": brand_name[:120],
        "normalized_brand_name": brand_name.casefold(),
        "category": category,
        "short_description": short_description,
        "data_type": "curated_commercial",
        "is_demo_product": False,
        "is_active": True,
        "suitable_skin_types": skin_types,
        "target_visible_concerns": concerns,
        "sensitivity_suitability": "potentially_suitable" if "sensitive_self_reported" in skin_types else "not_specified",
        "ingredients": parsed_ingredients,
        "normalized_ingredients": normalized,
        "highlighted_ingredients": highlighted,
        "fragrance_status": fragrance_status,
        "price": {"amount": inr_amount, "currency": "INR"},
        "package_size": {"quantity": 50 if "cream" in product_name.lower() or "moisturizer" in category else 100, "unit": "g" if "cream" in product_name.lower() else "ml"},
        "rating": {"value": min(5.0, max(0.0, rating_val)), "count": 120},
        "country_codes": ["IN", "US"],
        "availability_status": "available",
        "source_name": "Sephora Skincare Dataset (Kaggle)",
    }
    return product_doc


def import_kaggle_dataset():
    base_dir = Path(__file__).resolve().parent.parent.parent
    csv_path = base_dir / "data" / "products" / "kaggle_cosmetics.csv"
    if not csv_path.exists():
        logger.error("Dataset not found at %s", csv_path)
        return

    logger.info("Reading Kaggle cosmetics CSV...")
    with csv_path.open("r", encoding="utf-8-sig", errors="ignore") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    logger.info("Total rows read: %d", len(rows))

    products = []
    brands_map = {}

    for idx, row in enumerate(rows, start=1):
        doc = process_kaggle_row(row, idx)
        if doc:
            products.append(doc)
            b_id = doc["brand_id"]
            if b_id not in brands_map:
                brands_map[b_id] = {
                    "brand_id": b_id,
                    "brand_name": doc["brand_name"],
                    "slug": slugify(doc["brand_name"]),
                    "normalized_name": doc["normalized_brand_name"],
                    "country_of_origin": "US",
                    "product_count": 0,
                    "is_active": True,
                }
            brands_map[b_id]["product_count"] += 1

    logger.info("Successfully processed %d valid products across %d brands!", len(products), len(brands_map))

    settings = get_settings()
    client = pymongo.MongoClient(settings.mongodb_url)

    target_dbs = ["dermascan_ai", "dermascan"]
    for db_name in target_dbs:
        db = client[db_name]
        logger.info("Importing into database '%s'...", db_name)

        # Upsert brands
        for brand in brands_map.values():
            db.brands.update_one(
                {"brand_id": brand["brand_id"]},
                {"$set": brand},
                upsert=True,
            )

        # Upsert products (by slug / product_id)
        imported_count = 0
        for product in products:
            db.products.update_one(
                {"slug": product["slug"]},
                {"$set": product},
                upsert=True,
            )
            imported_count += 1

        total_in_db = db.products.count_documents({})
        total_brands_in_db = db.brands.count_documents({})
        logger.info("Finished '%s': %d products, %d brands now in collection!", db_name, total_in_db, total_brands_in_db)

    print("\n" + "=" * 60)
    print("  KAGGLE COSMETICS DATASET IMPORT COMPLETED SUCCESSFULLY!")
    print(f"  * Total Products Processed: {len(products)}")
    print(f"  * Total Unique Brands:     {len(brands_map)}")
    print("=" * 60)


if __name__ == "__main__":
    import_kaggle_dataset()
