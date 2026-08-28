from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.auth import clean_text
from app.schemas.user import ALLOWED_AGE_GROUPS

ALLOWED_BEHAVIOUR_LEVELS = ("Low", "Moderate", "High", "Not sure")
ALLOWED_FRAGRANCE_PREFERENCES = (
    "Fragrance-free only",
    "Prefer fragrance-free",
    "No preference",
)
ALLOWED_EXPERIENCE_LEVELS = ("Beginner", "Intermediate", "Advanced")
MAX_BUDGET_INR = 1_000_000
MAX_ARRAY_ITEMS = 20
MAX_ARRAY_ITEM_LENGTH = 80
MAX_NOTES_LENGTH = 1000

ProfileList = Annotated[list[str], Field(max_length=MAX_ARRAY_ITEMS)]


def normalize_string_list(values: Any) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValueError("Value must be a list of text items.")

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise ValueError("Each list item must be text.")
        item = clean_text(value)
        if not item:
            continue
        if len(item) > MAX_ARRAY_ITEM_LENGTH:
            raise ValueError(f"Each list item must be {MAX_ARRAY_ITEM_LENGTH} characters or fewer.")
        key = item.casefold()
        if key not in seen:
            seen.add(key)
            normalized.append(item)

    if len(normalized) > MAX_ARRAY_ITEMS:
        raise ValueError(f"No more than {MAX_ARRAY_ITEMS} items are allowed.")
    return normalized


class SkinProfilePayload(BaseModel):
    age_group: str
    oiliness_level: str
    dryness_level: str
    is_sensitive: bool | None
    known_allergies: ProfileList = Field(default_factory=list)
    current_products: ProfileList = Field(default_factory=list)
    budget_min: float | None = Field(default=None, ge=0, le=MAX_BUDGET_INR)
    budget_max: float | None = Field(default=None, ge=0, le=MAX_BUDGET_INR)
    preferred_brands: ProfileList = Field(default_factory=list)
    ingredients_to_avoid: ProfileList = Field(default_factory=list)
    fragrance_preference: str
    country: str = Field(..., min_length=1, max_length=120)
    experience_level: str
    additional_notes: str | None = Field(default=None, max_length=MAX_NOTES_LENGTH)

    model_config = ConfigDict(extra="forbid")

    @field_validator(
        "age_group",
        "oiliness_level",
        "dryness_level",
        "fragrance_preference",
        "country",
        "experience_level",
        mode="before",
    )
    @classmethod
    def sanitize_required_text(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("A text value is required.")
        return clean_text(value)

    @field_validator("additional_notes", mode="before")
    @classmethod
    def sanitize_optional_text(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Additional notes must be plain text.")
        cleaned = clean_text(value)
        return cleaned or None

    @field_validator(
        "known_allergies",
        "current_products",
        "preferred_brands",
        "ingredients_to_avoid",
        mode="before",
    )
    @classmethod
    def sanitize_lists(cls, value: Any) -> list[str]:
        return normalize_string_list(value)

    @model_validator(mode="after")
    def validate_profile(self) -> "SkinProfilePayload":
        if self.age_group not in ALLOWED_AGE_GROUPS:
            raise ValueError("Age group is not supported.")
        if self.oiliness_level not in ALLOWED_BEHAVIOUR_LEVELS:
            raise ValueError("Oiliness level is not supported.")
        if self.dryness_level not in ALLOWED_BEHAVIOUR_LEVELS:
            raise ValueError("Dryness level is not supported.")
        if self.fragrance_preference not in ALLOWED_FRAGRANCE_PREFERENCES:
            raise ValueError("Fragrance preference is not supported.")
        if self.experience_level not in ALLOWED_EXPERIENCE_LEVELS:
            raise ValueError("Experience level is not supported.")

        has_minimum = self.budget_min is not None
        has_maximum = self.budget_max is not None
        if has_minimum != has_maximum:
            raise ValueError("Provide both budget values or select no specific budget.")
        if has_minimum and self.budget_max < self.budget_min:
            raise ValueError("Maximum budget must be greater than or equal to minimum budget.")
        return self


class SkinProfileCreate(SkinProfilePayload):
    pass


class SkinProfileUpdate(SkinProfilePayload):
    pass


class SkinProfileResponse(SkinProfilePayload):
    id: str
    user_id: str
    is_complete: bool
    created_at: datetime
    updated_at: datetime


class SkinProfileCompletionResponse(BaseModel):
    exists: bool
    is_complete: bool
    next_route: str


class SkinProfileDeleteResponse(BaseModel):
    message: str
