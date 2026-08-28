from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.schemas.pagination import PaginationMetadata


def clean_text(value: str) -> str:
    return " ".join(value.split())


class BrandCreate(BaseModel):
    brand_id: str = Field(pattern=r"^BRD-[A-Z0-9-]{3,30}$")
    brand_name: str = Field(min_length=2, max_length=100)
    country_of_origin: str | None = Field(default=None, max_length=80)
    official_website: str | None = Field(default=None, max_length=500)
    is_verified: bool = False
    is_active: bool = True

    @field_validator("brand_name", "country_of_origin")
    @classmethod
    def sanitize_text(cls, value: str | None) -> str | None:
        return clean_text(value) if value else value

    @field_validator("official_website")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value and not value.lower().startswith(("https://", "http://")):
            raise ValueError("URL must use HTTP or HTTPS.")
        return value


class BrandResponse(BaseModel):
    brand_id: str
    brand_name: str
    country_of_origin: str | None = None
    official_website: str | None = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class BrandListResponse(BaseModel):
    items: list[BrandResponse]
    pagination: PaginationMetadata


def brand_document_to_response(document: dict[str, Any]) -> BrandResponse:
    return BrandResponse(**{key: value for key, value in document.items() if key != "_id"})
