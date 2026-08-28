from datetime import datetime
from typing import Any

from bson import ObjectId

from app.schemas.skin_profile import SkinProfilePayload, SkinProfileResponse


def build_skin_profile_document(
    *, user_id: str, payload: SkinProfilePayload, created_at: datetime
) -> dict[str, Any]:
    return {
        "user_id": ObjectId(user_id),
        **payload.model_dump(),
        "is_complete": True,
        "created_at": created_at,
        "updated_at": created_at,
    }


def skin_profile_document_to_response(
    document: dict[str, Any],
) -> SkinProfileResponse:
    return SkinProfileResponse(
        id=str(document["_id"]),
        user_id=str(document["user_id"]),
        age_group=document["age_group"],
        oiliness_level=document["oiliness_level"],
        dryness_level=document["dryness_level"],
        is_sensitive=document["is_sensitive"],
        known_allergies=document.get("known_allergies", []),
        current_products=document.get("current_products", []),
        budget_min=document.get("budget_min"),
        budget_max=document.get("budget_max"),
        preferred_brands=document.get("preferred_brands", []),
        ingredients_to_avoid=document.get("ingredients_to_avoid", []),
        fragrance_preference=document["fragrance_preference"],
        country=document["country"],
        experience_level=document["experience_level"],
        additional_notes=document.get("additional_notes"),
        is_complete=document.get("is_complete", False),
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )
