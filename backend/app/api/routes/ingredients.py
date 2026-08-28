from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_ingredients_collection, get_products_collection
from app.core.catalogue import INGREDIENT_CATEGORIES, PUBLIC_DATA_TYPES
from app.repositories.ingredient_repository import (
    find_ingredient,
    ingredient_search_query,
    list_ingredients,
)
from app.schemas.ingredient import (
    IngredientDetailResponse,
    IngredientListResponse,
    IngredientProductReference,
    ingredient_document_to_response,
)
from app.schemas.pagination import pagination_metadata

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("", response_model=IngredientListResponse)
async def read_ingredients(
    search: str | None = Query(None, max_length=100),
    ingredient_category: Literal[*INGREDIENT_CATEGORIES] | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    collection=Depends(get_ingredients_collection),
) -> IngredientListResponse:
    documents, total = await list_ingredients(
        collection, ingredient_search_query(search, ingredient_category), page, page_size
    )
    return IngredientListResponse(
        items=[ingredient_document_to_response(document) for document in documents],
        pagination=pagination_metadata(page, page_size, total),
    )


@router.get("/{ingredient_id}", response_model=IngredientDetailResponse)
async def read_ingredient(
    ingredient_id: str,
    ingredients=Depends(get_ingredients_collection),
    products=Depends(get_products_collection),
) -> IngredientDetailResponse:
    document = await find_ingredient(ingredients, ingredient_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Ingredient not found.")
    cursor = (
        products.find(
            {
                "normalized_ingredients": document["normalized_name"],
                "is_active": True,
                "data_type": {"$in": list(PUBLIC_DATA_TYPES)},
            }
        )
        .sort("product_name", 1)
        .limit(20)
    )
    matches = await cursor.to_list(length=20)
    base = ingredient_document_to_response(document).model_dump()
    return IngredientDetailResponse(
        **base,
        products=[
            IngredientProductReference(
                **{
                    key: product[key]
                    for key in (
                        "product_id",
                        "product_name",
                        "brand_name",
                        "category",
                        "is_demo_product",
                    )
                }
            )
            for product in matches
        ],
        disclaimer="Ingredient roles are general catalogue information. Individual tolerance varies and this page is not medical advice.",
    )
