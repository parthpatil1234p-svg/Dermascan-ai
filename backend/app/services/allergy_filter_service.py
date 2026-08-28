from typing import Any

from app.models.product import normalize_key
from app.rules.allergy_rules import ALLERGY_ALIASES, ALLERGY_PRODUCT_FLAGS
from app.schemas.product_eligibility import EligibilityReason, NormalizedAllergy


def normalize_allergies(
    values: list[str], ingredient_lookup: dict[str, dict[str, Any]]
) -> list[NormalizedAllergy]:
    output: list[NormalizedAllergy] = []
    seen: set[tuple[str | None, str]] = set()
    for original in values:
        key = normalize_key(original)
        normalized = ALLERGY_ALIASES.get(key)
        if normalized is None and key in ingredient_lookup:
            normalized = ingredient_lookup[key]["normalized_name"]
        marker = (normalized, key)
        if marker in seen:
            continue
        seen.add(marker)
        output.append(
            NormalizedAllergy(
                original=" ".join(original.split()),
                normalized=normalized,
                mapping_status="mapped" if normalized else "unmapped",
            )
        )
    return output


def evaluate_allergies(
    product: dict[str, Any],
    allergies: list[NormalizedAllergy],
    ingredient_lookup: dict[str, dict[str, Any]],
) -> tuple[list[EligibilityReason], list[EligibilityReason]]:
    exclusions: list[EligibilityReason] = []
    cautions: list[EligibilityReason] = []
    product_ingredients = set(product.get("normalized_ingredients", []))
    product_flags = set(product.get("potential_irritant_flags", []))
    allergen_flags = {normalize_key(value) for value in product.get("allergen_flags", [])}
    for allergy in allergies:
        key = normalize_key(allergy.original)
        concept = allergy.normalized
        matched = False
        if concept == "added_fragrance":
            matched = (
                product.get("fragrance_status")
                in {"contains_added_fragrance", "contains_fragrant_ingredients"}
                or "fragrance" in product_ingredients
            )
        elif concept == "essential_oil":
            matched = "contains_essential_oils" in product_flags or any(
                ingredient_lookup.get(name, {}).get("ingredient_category") == "essential_oil"
                for name in product_ingredients
            )
        elif concept in ALLERGY_PRODUCT_FLAGS:
            matched = bool(product_flags & ALLERGY_PRODUCT_FLAGS[concept])
        elif concept:
            matched = concept in product_ingredients or concept in allergen_flags
        else:
            matched = key in product_ingredients or key in allergen_flags

        if matched:
            exclusions.append(
                EligibilityReason(
                    code="KNOWN_ALLERGY_MATCH",
                    message="This product was excluded because its ingredient data matches an allergy you reported.",
                    matched_value=allergy.original,
                )
            )
        elif allergy.mapping_status == "unmapped":
            cautions.append(
                EligibilityReason(
                    code="POTENTIAL_ALLERGEN_PRESENT",
                    message="Your allergy entry could not be matched to the ingredient taxonomy. Review the current product label carefully before use.",
                    matched_value=allergy.original,
                )
            )
    return exclusions, cautions
