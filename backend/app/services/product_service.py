from datetime import datetime, timedelta, timezone
from typing import Any

from pymongo.errors import DuplicateKeyError

from app.core.catalogue import CATEGORY_DISPLAY_NAMES
from app.core.config import Settings
from app.models.product import build_product_document
from app.repositories.product_repository import (
    find_product,
    insert_product,
    list_products,
    replace_product,
    update_product,
)
from app.schemas.pagination import pagination_metadata
from app.schemas.product import (
    ProductCreate,
    ProductDetailResponse,
    ProductListResponse,
    ProductPatch,
    ProductSummaryResponse,
)
from app.services.product_search_service import ProductFilters, build_product_query, get_sort
from app.services.product_validation_service import DuplicateProductError, find_potential_duplicate


class ProductNotFoundError(Exception):
    pass


DISCLAIMER = (
    "Catalogue mappings support general skincare discovery only. They do not establish "
    "medical suitability, allergy safety, treatment, or guaranteed results."
)


def _is_stale(value: datetime | None, days: int) -> bool:
    if value is None:
        return True
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value < datetime.now(timezone.utc) - timedelta(days=days)


def product_summary(document: dict[str, Any], settings: Settings) -> ProductSummaryResponse:
    return ProductSummaryResponse(
        product_id=document["product_id"],
        slug=document["slug"],
        product_name=document["product_name"],
        brand_id=document["brand_id"],
        brand_name=document["brand_name"],
        category=document["category"],
        category_display=CATEGORY_DISPLAY_NAMES[document["category"]],
        short_description=document["short_description"],
        data_type=document["data_type"],
        is_demo_product=document["is_demo_product"],
        demo_label=(
            "Demonstration Product - Not a Real Retail Listing"
            if document["is_demo_product"]
            else None
        ),
        suitable_skin_types=document["suitable_skin_types"],
        target_visible_concerns=document.get("target_visible_concerns", []),
        highlighted_ingredients=document.get("highlighted_ingredients", []),
        fragrance_status=document.get("fragrance_status", "unknown"),
        price=document.get("price"),
        price_checked_at=document.get("price_checked_at"),
        price_is_stale=_is_stale(
            document.get("price_checked_at"), settings.product_price_stale_days
        ),
        country_codes=document.get("country_codes", []),
        availability_status=document.get("availability_status", "unknown"),
        availability_checked_at=document.get("availability_checked_at"),
        availability_is_stale=_is_stale(
            document.get("availability_checked_at"), settings.product_availability_stale_days
        ),
    )


def product_detail(document: dict[str, Any], settings: Settings) -> ProductDetailResponse:
    summary = product_summary(document, settings).model_dump()
    return ProductDetailResponse(
        **summary,
        compatibility_notes=document.get("compatibility_notes", []),
        sensitivity_suitability=document.get("sensitivity_suitability", "not_specified"),
        ingredients=document.get("ingredients", []),
        normalized_ingredients=document.get("normalized_ingredients", []),
        potential_irritant_flags=document.get("potential_irritant_flags", []),
        allergen_flags=document.get("allergen_flags", []),
        essential_oil_status=document.get("essential_oil_status", "unknown"),
        comedogenic_claim_status=document.get("comedogenic_claim_status", "not_specified"),
        minimum_age_group=document.get("minimum_age_group", "Not specified"),
        maximum_age_group=document.get("maximum_age_group", "Not specified"),
        usage_time=document.get("usage_time", "not_specified"),
        usage_frequency=document.get("usage_frequency"),
        package_size=document.get("package_size"),
        price_per_unit=document.get("price_per_unit"),
        price_source=document.get("price_source"),
        source_name=document["source_name"],
        official_product_url=document.get("official_product_url"),
        source_verified_at=document["source_verified_at"],
        source_is_stale=_is_stale(
            document["source_verified_at"], settings.product_source_verification_stale_days
        ),
        rating=document.get("rating"),
        general_disclaimer=DISCLAIMER,
    )


async def search_products(
    collection: Any,
    filters: ProductFilters,
    sort: str,
    page: int,
    page_size: int,
    settings: Settings,
) -> ProductListResponse:
    documents, total = await list_products(
        collection, build_product_query(filters), get_sort(sort), page, page_size
    )
    return ProductListResponse(
        items=[product_summary(document, settings) for document in documents],
        pagination=pagination_metadata(page, page_size, total),
    )


async def get_public_product(
    collection: Any, identifier: str, settings: Settings
) -> ProductDetailResponse:
    document = await find_product(collection, identifier)
    if document is None or document.get("data_type") == "unverified_draft":
        raise ProductNotFoundError
    return product_detail(document, settings)


async def create_catalogue_product(
    collection: Any, payload: ProductCreate, settings: Settings
) -> ProductDetailResponse:
    if await find_potential_duplicate(collection, payload):
        raise DuplicateProductError
    document = build_product_document(payload, datetime.now(timezone.utc))
    try:
        await insert_product(collection, document)
    except DuplicateKeyError as exc:
        raise DuplicateProductError from exc
    return product_detail(document, settings)


async def replace_catalogue_product(
    collection: Any, product_id: str, payload: ProductCreate, settings: Settings
) -> ProductDetailResponse:
    existing = await find_product(collection, product_id, include_inactive=True)
    if existing is None:
        raise ProductNotFoundError
    document = build_product_document(payload, existing["created_at"])
    document["updated_at"] = datetime.now(timezone.utc)
    await replace_product(collection, product_id, document)
    return product_detail(document, settings)


async def patch_catalogue_product(
    collection: Any, product_id: str, payload: ProductPatch, settings: Settings
) -> ProductDetailResponse:
    existing = await find_product(collection, product_id, include_inactive=True)
    if existing is None:
        raise ProductNotFoundError
    fields = payload.model_dump(exclude_unset=True, mode="python")
    fields["updated_at"] = datetime.now(timezone.utc)
    await update_product(collection, product_id, fields)
    existing.update(fields)
    return product_detail(existing, settings)


async def soft_delete_product(collection: Any, product_id: str) -> None:
    if not await update_product(
        collection, product_id, {"is_active": False, "updated_at": datetime.now(timezone.utc)}
    ):
        raise ProductNotFoundError
