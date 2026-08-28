from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_products_collection
from app.core.catalogue import (
    AVAILABILITY_STATUSES,
    FRAGRANCE_STATUSES,
    PRODUCT_CATEGORIES,
    PUBLIC_DATA_TYPES,
    SKIN_TYPES,
    SORT_OPTIONS,
    VISIBLE_CONCERNS,
)
from app.core.config import Settings, get_settings
from app.schemas.product import ProductDetailResponse, ProductListResponse
from app.services.product_search_service import ProductFilters
from app.services.product_service import ProductNotFoundError, get_public_product, search_products

router = APIRouter(prefix="/products", tags=["product catalogue"])


@router.get("", response_model=ProductListResponse)
async def list_catalogue_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    brand: str | None = Query(None, max_length=100),
    category: Literal[*PRODUCT_CATEGORIES] | None = None,
    skin_type: Literal[*SKIN_TYPES] | None = None,
    visible_concern: Literal[*VISIBLE_CONCERNS] | None = None,
    ingredient: str | None = Query(None, min_length=1, max_length=100),
    exclude_ingredient: str | None = Query(None, min_length=1, max_length=100),
    country: str | None = Query(None, min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$"),
    availability: Literal[*AVAILABILITY_STATUSES] | None = None,
    min_price: float | None = Query(None, ge=0, le=1_000_000),
    max_price: float | None = Query(None, ge=0, le=1_000_000),
    fragrance_status: Literal[*FRAGRANCE_STATUSES] | None = None,
    data_type: Literal[*PUBLIC_DATA_TYPES] | None = None,
    sort: Literal[*SORT_OPTIONS] = "name_asc",
    collection=Depends(get_products_collection),
    settings: Settings = Depends(get_settings),
) -> ProductListResponse:
    if min_price is not None and max_price is not None and max_price < min_price:
        raise HTTPException(
            status_code=422, detail="Maximum price must be greater than or equal to minimum price."
        )
    filters = ProductFilters(
        search=search,
        brand=brand,
        category=category,
        skin_type=skin_type,
        visible_concern=visible_concern,
        ingredient=ingredient,
        exclude_ingredient=exclude_ingredient,
        country=country,
        availability=availability,
        min_price=min_price,
        max_price=max_price,
        fragrance_status=fragrance_status,
        data_type=data_type,
    )
    return await search_products(collection, filters, sort, page, page_size, settings)


@router.get("/{product_id}", response_model=ProductDetailResponse)
async def read_catalogue_product(
    product_id: str,
    collection=Depends(get_products_collection),
    settings: Settings = Depends(get_settings),
) -> ProductDetailResponse:
    try:
        return await get_public_product(collection, product_id, settings)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Product not found.") from exc
