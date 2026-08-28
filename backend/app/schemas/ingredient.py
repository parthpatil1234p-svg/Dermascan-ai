from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.core.catalogue import INGREDIENT_CATEGORIES
from app.schemas.brand import clean_text
from app.schemas.pagination import PaginationMetadata

IngredientCategory = Literal[*INGREDIENT_CATEGORIES]


def unique_clean_strings(values: list[str], *, maximum: int = 30) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for raw in values[:maximum]:
        value = clean_text(raw)
        key = value.casefold()
        if value and key not in seen:
            output.append(value)
            seen.add(key)
    return output


class IngredientCreate(BaseModel):
    ingredient_id: str = Field(pattern=r"^ING-[A-Z0-9-]{3,30}$")
    canonical_name: str = Field(min_length=2, max_length=100)
    aliases: list[str] = Field(default_factory=list, max_length=30)
    ingredient_category: IngredientCategory
    common_skincare_roles: list[str] = Field(default_factory=list, max_length=20)
    suitability_notes: list[str] = Field(default_factory=list, max_length=20)
    caution_notes: list[str] = Field(default_factory=list, max_length=20)
    is_active: bool = True

    @field_validator("canonical_name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        return clean_text(value)

    @field_validator("aliases", "common_skincare_roles", "suitability_notes", "caution_notes")
    @classmethod
    def sanitize_lists(cls, values: list[str]) -> list[str]:
        return unique_clean_strings(values)


class IngredientResponse(BaseModel):
    ingredient_id: str
    canonical_name: str
    aliases: list[str]
    ingredient_category: IngredientCategory
    common_skincare_roles: list[str]
    suitability_notes: list[str]
    caution_notes: list[str]
    created_at: datetime
    updated_at: datetime


class IngredientListResponse(BaseModel):
    items: list[IngredientResponse]
    pagination: PaginationMetadata


class IngredientProductReference(BaseModel):
    product_id: str
    product_name: str
    brand_name: str
    category: str
    is_demo_product: bool


class IngredientDetailResponse(IngredientResponse):
    products: list[IngredientProductReference] = Field(default_factory=list)
    disclaimer: str


def ingredient_document_to_response(document: dict[str, Any]) -> IngredientResponse:
    public = {
        key: value
        for key, value in document.items()
        if key not in {"_id", "normalized_name", "is_active"}
    }
    return IngredientResponse(**public)
