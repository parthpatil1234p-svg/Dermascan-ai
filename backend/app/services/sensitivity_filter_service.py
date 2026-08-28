from typing import Any

from app.rules.ingredient_rules import ACTIVE_CAUTION_FLAGS
from app.schemas.product_eligibility import EligibilityReason


def evaluate_sensitivity(product: dict[str, Any], is_sensitive: bool | None):
    cautions: list[EligibilityReason] = []
    positives: list[EligibilityReason] = []
    if is_sensitive is not True:
        return cautions, positives
    suitability = product.get("sensitivity_suitability", "unknown")
    if suitability == "potentially_suitable":
        positives.append(
            EligibilityReason(
                code="SENSITIVITY_POTENTIALLY_SUITABLE",
                message="The catalogue marks this product as potentially suitable for self-reported sensitivity; this is not an allergy guarantee.",
            )
        )
    elif suitability == "use_with_caution":
        cautions.append(
            EligibilityReason(
                code="SENSITIVITY_USE_WITH_CAUTION",
                message="You reported sensitivity and the catalogue marks this product for cautious use.",
            )
        )
    else:
        cautions.append(
            EligibilityReason(
                code="SENSITIVITY_NOT_SPECIFIED",
                message="You reported sensitivity, but sensitivity suitability is not established in this catalogue record.",
            )
        )
    for flag in dict.fromkeys(product.get("potential_irritant_flags", [])):
        if flag in ACTIVE_CAUTION_FLAGS:
            code, message = ACTIVE_CAUTION_FLAGS[flag]
            cautions.append(EligibilityReason(code=code, message=message))
    return cautions, positives


def evaluate_fragrance(product: dict[str, Any], preference: str):
    exclusions: list[EligibilityReason] = []
    cautions: list[EligibilityReason] = []
    gaps: list[EligibilityReason] = []
    status = product.get("fragrance_status", "unknown")
    contains = status in {"contains_added_fragrance", "contains_fragrant_ingredients"}
    if preference == "fragrance_free_only":
        if contains:
            exclusions.append(
                EligibilityReason(
                    code="FRAGRANCE_CONFLICT",
                    message="This product was excluded because you selected fragrance-free products only.",
                    matched_value=status,
                )
            )
        elif status == "unknown":
            gaps.append(
                EligibilityReason(
                    code="FRAGRANCE_CONFLICT",
                    message="Fragrance status is unknown, so this product cannot be safely evaluated against your fragrance-free-only preference.",
                )
            )
    elif preference == "prefer_fragrance_free" and contains:
        cautions.append(
            EligibilityReason(
                code="FRAGRANCE_CONFLICT",
                message="This product contains fragrance, while you prefer fragrance-free products.",
                matched_value=status,
            )
        )
    return exclusions, cautions, gaps
