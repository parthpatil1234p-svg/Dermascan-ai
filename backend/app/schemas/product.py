from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.catalogue import (
    AGE_GROUPS,
    AVAILABILITY_STATUSES,
    CAUTION_FLAGS,
    DATA_TYPES,
    ESSENTIAL_OIL_STATUSES,
    FRAGRANCE_STATUSES,
    PRODUCT_CATEGORIES,
    SENSITIVITY_SUITABILITY,
    SKIN_TYPES,
    SUPPORTED_CURRENCIES,
    USAGE_TIMES,
    VISIBLE_CONCERNS,
)
from app.schemas.brand import clean_text
from app.schemas.ingredient import unique_clean_strings
from app.schemas.pagination import PaginationMetadata

ProductCategory = Literal[*PRODUCT_CATEGORIES]
SkinType = Literal[*SKIN_TYPES]
VisibleConcern = Literal[*VISIBLE_CONCERNS]
DataType = Literal[*DATA_TYPES]
AvailabilityStatus = Literal[*AVAILABILITY_STATUSES]
FragranceStatus = Literal[*FRAGRANCE_STATUSES]
SensitivitySuitability = Literal[*SENSITIVITY_SUITABILITY]


class ProductIngredient(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
    position: int = Field(ge=1, le=300)

    @field_validator("display_name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        return clean_text(value)


class Money(BaseModel):
    amount: float = Field(ge=0, le=1_000_000)
    currency: Literal[*SUPPORTED_CURRENCIES] = "INR"


class PackageSize(BaseModel):
    quantity: float = Field(gt=0, le=100_000)
    unit: Literal["ml", "g", "unit"]


class PricePerUnit(BaseModel):
    amount: float = Field(ge=0, le=1_000_000)
    unit: Literal["ml", "g", "unit"]


class RatingData(BaseModel):
    value: float = Field(ge=0, le=5)
    count: int = Field(ge=0)
    source: str = Field(min_length=2, max_length=120)
    checked_at: datetime


class ProductCreate(BaseModel):
    product_id: str = Field(pattern=r"^PRD-[A-Z0-9-]{3,30}$")
    slug: str | None = Field(default=None, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    product_name: str = Field(min_length=2, max_length=160)
    brand_id: str = Field(pattern=r"^BRD-[A-Z0-9-]{3,30}$")
    brand_name: str = Field(min_length=2, max_length=100)
    category: ProductCategory
    short_description: str = Field(min_length=10, max_length=600)
    data_type: DataType
    is_demo_product: bool
    suitable_skin_types: list[SkinType] = Field(min_length=1, max_length=6)
    target_visible_concerns: list[VisibleConcern] = Field(default_factory=list, max_length=10)
    compatibility_notes: list[str] = Field(default_factory=list, max_length=10)
    sensitivity_suitability: SensitivitySuitability = "not_specified"
    ingredients: list[ProductIngredient] = Field(default_factory=list, max_length=300)
    normalized_ingredients: list[str] = Field(default_factory=list, max_length=300)
    unmapped_ingredients: list[str] = Field(default_factory=list, max_length=100)
    highlighted_ingredients: list[str] = Field(default_factory=list, max_length=20)
    potential_irritant_flags: list[Literal[*CAUTION_FLAGS]] = Field(default_factory=list)
    allergen_flags: list[str] = Field(default_factory=list, max_length=30)
    fragrance_status: FragranceStatus = "unknown"
    essential_oil_status: Literal[*ESSENTIAL_OIL_STATUSES] = "unknown"
    comedogenic_claim_status: Literal["claimed_non_comedogenic", "not_specified", "unknown"] = (
        "not_specified"
    )
    minimum_age_group: Literal[*AGE_GROUPS] = "Not specified"
    maximum_age_group: Literal[*AGE_GROUPS] = "Not specified"
    usage_time: Literal[*USAGE_TIMES] = "not_specified"
    usage_frequency: str | None = Field(default=None, max_length=120)
    price: Money | None = None
    package_size: PackageSize | None = None
    price_per_unit: PricePerUnit | None = None
    price_checked_at: datetime | None = None
    price_source: str | None = Field(default=None, max_length=160)
    country_codes: list[str] = Field(default_factory=list, max_length=30)
    availability_status: AvailabilityStatus = "unknown"
    availability_checked_at: datetime | None = None
    official_product_url: str | None = Field(default=None, max_length=500)
    source_name: str = Field(min_length=2, max_length=160)
    source_url: str | None = Field(default=None, max_length=500)
    source_verified_at: datetime
    rating: RatingData | None = None
    is_active: bool = True

    @field_validator(
        "product_name",
        "brand_name",
        "short_description",
        "usage_frequency",
        "price_source",
        "source_name",
    )
    @classmethod
    def sanitize_text(cls, value: str | None) -> str | None:
        return clean_text(value) if value else value

    @field_validator(
        "compatibility_notes",
        "normalized_ingredients",
        "unmapped_ingredients",
        "highlighted_ingredients",
        "allergen_flags",
    )
    @classmethod
    def sanitize_string_lists(cls, values: list[str]) -> list[str]:
        return unique_clean_strings(values, maximum=300)

    @field_validator("suitable_skin_types", "target_visible_concerns", "potential_irritant_flags")
    @classmethod
    def unique_controlled_lists(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))

    @field_validator("country_codes")
    @classmethod
    def validate_country_codes(cls, values: list[str]) -> list[str]:
        output = list(dict.fromkeys(value.strip().upper() for value in values))
        if any(len(value) != 2 or not value.isalpha() for value in output):
            raise ValueError("Country codes must use two uppercase letters.")
        return output

    @field_validator("official_product_url", "source_url")
    @classmethod
    def validate_urls(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("URL must use HTTP or HTTPS.")
        return value

    @model_validator(mode="after")
    def validate_consistency(self) -> "ProductCreate":
        if (self.data_type == "demo_synthetic") != self.is_demo_product:
            raise ValueError("Demo products must use demo_synthetic data and the demo flag.")
        if self.price is not None and self.price_checked_at is None:
            raise ValueError("price_checked_at is required when price is provided.")
        if self.availability_status != "unknown" and self.availability_checked_at is None:
            raise ValueError("availability_checked_at is required for known availability.")
        positions = [item.position for item in self.ingredients]
        if len(positions) != len(set(positions)):
            raise ValueError("Ingredient positions must be unique.")
        return self


class ProductUpdate(ProductCreate):
    pass


class ProductPatch(BaseModel):
    product_name: str | None = Field(default=None, min_length=2, max_length=160)
    short_description: str | None = Field(default=None, min_length=10, max_length=600)
    availability_status: AvailabilityStatus | None = None
    availability_checked_at: datetime | None = None
    price: Money | None = None
    price_checked_at: datetime | None = None
    is_active: bool | None = None


class ProductSummaryResponse(BaseModel):
    product_id: str
    slug: str
    product_name: str
    brand_id: str
    brand_name: str
    category: ProductCategory
    category_display: str
    short_description: str
    data_type: DataType
    is_demo_product: bool
    demo_label: str | None = None
    suitable_skin_types: list[SkinType]
    target_visible_concerns: list[VisibleConcern]
    highlighted_ingredients: list[str]
    fragrance_status: FragranceStatus
    price: Money | None = None
    price_checked_at: datetime | None = None
    price_is_stale: bool
    country_codes: list[str]
    availability_status: AvailabilityStatus
    availability_checked_at: datetime | None = None
    availability_is_stale: bool


class ProductDetailResponse(ProductSummaryResponse):
    compatibility_notes: list[str]
    sensitivity_suitability: SensitivitySuitability
    ingredients: list[ProductIngredient]
    normalized_ingredients: list[str]
    potential_irritant_flags: list[str]
    allergen_flags: list[str]
    essential_oil_status: str
    comedogenic_claim_status: str
    minimum_age_group: str
    maximum_age_group: str
    usage_time: str
    usage_frequency: str | None = None
    package_size: PackageSize | None = None
    price_per_unit: PricePerUnit | None = None
    price_source: str | None = None
    source_name: str
    official_product_url: str | None = None
    source_verified_at: datetime
    source_is_stale: bool
    rating: RatingData | None = None
    general_disclaimer: str


class ProductListResponse(BaseModel):
    items: list[ProductSummaryResponse]
    pagination: PaginationMetadata


class ProductImportResponse(BaseModel):
    import_job_id: str
    status: Literal["preview_ready", "completed", "completed_with_errors", "failed"]
    total_records: int
    valid_records: int
    invalid_records: int
    duplicate_records: int
    inserted_records: int
    updated_records: int
    errors: list[str]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
