from typing import Any

from app.rules.age_rules import AGE_ORDER, UNDER_18_RESTRICTED_FLAGS
from app.schemas.product_eligibility import EligibilityReason


def evaluate_age(product: dict[str, Any], user_age_group: str) -> list[EligibilityReason]:
    exclusions: list[EligibilityReason] = []
    flags = set(product.get("potential_irritant_flags", []))
    if user_age_group == "Under 18" and flags & UNDER_18_RESTRICTED_FLAGS:
        exclusions.append(
            EligibilityReason(
                code="AGE_GROUP_RESTRICTION",
                message="This catalogue record is excluded by the project's conservative under-18 safety rule.",
            )
        )
    minimum = product.get("minimum_age_group", "Not specified")
    maximum = product.get("maximum_age_group", "Not specified")
    if user_age_group in AGE_ORDER:
        if minimum in AGE_ORDER and AGE_ORDER[user_age_group] < AGE_ORDER[minimum]:
            exclusions.append(
                EligibilityReason(
                    code="AGE_GROUP_RESTRICTION",
                    message="The product's verified age metadata does not include your selected age group.",
                )
            )
        if maximum in AGE_ORDER and AGE_ORDER[user_age_group] > AGE_ORDER[maximum]:
            exclusions.append(
                EligibilityReason(
                    code="AGE_GROUP_RESTRICTION",
                    message="The product's verified age metadata does not include your selected age group.",
                )
            )
    return exclusions
