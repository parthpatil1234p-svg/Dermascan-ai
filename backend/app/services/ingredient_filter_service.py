from typing import Any

from app.models.product import normalize_key
from app.rules.ingredient_rules import CATEGORY_ALIASES
from app.schemas.product_eligibility import EligibilityReason, NormalizedAvoidance


def normalize_avoidances(
    values: list[str], ingredient_lookup: dict[str, dict[str, Any]]
) -> list[NormalizedAvoidance]:
    output: list[NormalizedAvoidance] = []
    seen: set[tuple[str | None, str]] = set()
    for original in values:
        key = normalize_key(original)
        if key in CATEGORY_ALIASES:
            normalized, match_type = CATEGORY_ALIASES[key], "category"
        elif key in ingredient_lookup:
            normalized, match_type = ingredient_lookup[key]["normalized_name"], "ingredient"
        else:
            normalized, match_type = None, "unmapped"
        marker = (normalized, key)
        if marker not in seen:
            seen.add(marker)
            output.append(
                NormalizedAvoidance(
                    original=" ".join(original.split()),
                    normalized=normalized,
                    match_type=match_type,
                )
            )
    return output


def evaluate_avoided_ingredients(
    product: dict[str, Any],
    avoidances: list[NormalizedAvoidance],
    ingredient_lookup: dict[str, dict[str, Any]],
) -> tuple[list[EligibilityReason], list[EligibilityReason]]:
    exclusions: list[EligibilityReason] = []
    cautions: list[EligibilityReason] = []
    ingredients = product.get("normalized_ingredients", [])
    for avoidance in avoidances:
        matched_name: str | None = None
        if avoidance.match_type == "ingredient" and avoidance.normalized in ingredients:
            matched_name = ingredient_lookup.get(avoidance.normalized, {}).get(
                "canonical_name", avoidance.original
            )
        elif avoidance.match_type == "category":
            matched_name = next(
                (
                    ingredient_lookup[name]["canonical_name"]
                    for name in ingredients
                    if name in ingredient_lookup
                    and ingredient_lookup[name].get("ingredient_category") == avoidance.normalized
                ),
                None,
            )
        if matched_name:
            exclusions.append(
                EligibilityReason(
                    code="USER_AVOIDED_INGREDIENT_MATCH",
                    message="This product was excluded because it contains an ingredient you selected to avoid.",
                    matched_value=matched_name,
                )
            )
        elif avoidance.match_type == "unmapped":
            cautions.append(
                EligibilityReason(
                    code="INGREDIENT_DATA_INCOMPLETE",
                    message="One ingredient-avoidance entry could not be mapped to the catalogue taxonomy. Review the current label carefully.",
                    matched_value=avoidance.original,
                )
            )
    return exclusions, cautions
