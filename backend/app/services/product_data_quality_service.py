from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.catalogue import AVAILABILITY_STATUSES, PRODUCT_CATEGORIES, PUBLIC_DATA_TYPES
from app.core.config import Settings
from app.schemas.product_eligibility import EligibilityReason, UserFilteringContext


def evaluate_product_data_quality(
    product: dict[str, Any],
    context: UserFilteringContext,
    settings: Settings,
) -> tuple[list[EligibilityReason], list[EligibilityReason], list[EligibilityReason]]:
    exclusions: list[EligibilityReason] = []
    cautions: list[EligibilityReason] = []
    gaps: list[EligibilityReason] = []
    if not product.get("is_active", False):
        exclusions.append(
            EligibilityReason(
                code="PRODUCT_INACTIVE", message="This inactive catalogue record is not eligible."
            )
        )
    if product.get("data_type") not in PUBLIC_DATA_TYPES:
        exclusions.append(
            EligibilityReason(
                code="PRODUCT_UNVERIFIED",
                message="This unverified catalogue record is not eligible.",
            )
        )
    if product.get("category") not in PRODUCT_CATEGORIES:
        gaps.append(
            EligibilityReason(
                code="CATEGORY_NOT_ALLOWED",
                message="The product category is unsupported or invalid.",
            )
        )
    if (product.get("data_type") == "demo_synthetic") != bool(product.get("is_demo_product")):
        gaps.append(
            EligibilityReason(
                code="PRODUCT_DATA_CONTRADICTION",
                message="The product has contradictory demonstration-data fields.",
            )
        )
    if product.get("availability_status") not in AVAILABILITY_STATUSES:
        gaps.append(
            EligibilityReason(
                code="PRODUCT_DATA_CONTRADICTION",
                message="The product has invalid availability metadata.",
            )
        )
    price = product.get("price")
    if price and float(price.get("amount", -1)) < 0:
        gaps.append(
            EligibilityReason(
                code="PRODUCT_DATA_CONTRADICTION", message="The product has invalid price metadata."
            )
        )
    needs_ingredients = bool(context.known_allergies or context.ingredients_to_avoid)
    if needs_ingredients and not product.get("ingredients"):
        gaps.append(
            EligibilityReason(
                code="INGREDIENT_LIST_MISSING",
                message="Ingredient information is missing while allergy or avoidance checks are required.",
            )
        )
    if product.get("unmapped_ingredients"):
        gaps.append(
            EligibilityReason(
                code="UNMAPPED_CRITICAL_INGREDIENT",
                message="Some source ingredients could not be mapped to the controlled taxonomy.",
            )
        )
    if product.get("is_demo_product"):
        cautions.append(
            EligibilityReason(
                code="DEMO_PRODUCT",
                message="This is a fictional demonstration product, not a real retail listing.",
            )
        )
    verified = product.get("source_verified_at")
    if verified is None or verified < datetime.now(timezone.utc) - timedelta(
        days=settings.product_source_verification_stale_days
    ):
        cautions.append(
            EligibilityReason(
                code="SOURCE_DATA_STALE", message="The product source record may be outdated."
            )
        )
    return exclusions, cautions, gaps
