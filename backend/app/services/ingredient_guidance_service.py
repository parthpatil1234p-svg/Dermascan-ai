from typing import Any

from app.schemas.final_report import IngredientGuidance, IngredientGuidanceItem

ROLE_RULES = {
    "Dry": ("Humectant and barrier support", "May support hydration for dry-looking areas."),
    "Oily": ("Oil-balance support", "May be relevant to the visible oiliness evidence."),
    "Combination": (
        "Balanced hydration support",
        "May support hydration without assuming one uniform skin behavior.",
    ),
    "Normal": ("Barrier maintenance", "May support a simple maintenance-focused routine."),
    "Uncertain": (
        "Gentle barrier support",
        "A broad gentle role is used because the skin-type estimate was uncertain.",
    ),
}
CONCERN_RULES = {
    "visible_dryness": ("Humectant", "May support hydration for dry-looking areas."),
    "dry_looking_areas": ("Humectant", "May support hydration for dry-looking areas."),
    "visible_oiliness": ("Oil-balance support", "May be relevant to visible oiliness."),
    "dull_looking_appearance": (
        "Antioxidant support",
        "May be relevant to a dull-looking appearance.",
    ),
    "uneven_looking_tone": ("Antioxidant support", "May be relevant to an uneven-looking tone."),
    "visible_pores": (
        "Gentle exfoliating support",
        "May be relevant where visible pores were observed; introduce cautiously.",
    ),
}
ROLE_EXAMPLES = {
    "Humectant": ["Glycerin", "Hyaluronic Acid"],
    "Humectant and barrier support": ["Glycerin", "Ceramides"],
    "Oil-balance support": ["Niacinamide"],
    "Balanced hydration support": ["Glycerin", "Niacinamide"],
    "Barrier maintenance": ["Ceramides", "Squalane"],
    "Gentle barrier support": ["Glycerin", "Ceramides"],
    "Antioxidant support": ["Vitamin C derivatives", "Vitamin E"],
    "Gentle exfoliating support": ["Salicylic Acid"],
}


def build_ingredient_guidance(
    profile: dict[str, Any],
    skin_type: dict[str, Any] | None,
    concerns: dict[str, Any] | None,
) -> IngredientGuidance:
    skin_value = (skin_type or {}).get("final_skin_type", "Uncertain")
    role, reason = ROLE_RULES.get(skin_value, ROLE_RULES["Uncertain"])
    relevant = [
        IngredientGuidanceItem(
            ingredient_role=role,
            examples=ROLE_EXAMPLES[role],
            reason=reason,
        )
    ]
    seen_roles = {role.casefold()}
    for result in (concerns or {}).get("concern_results", []):
        if result.get("status") not in {"observed", "possible"}:
            continue
        rule = CONCERN_RULES.get(result.get("concern_code"))
        if rule and rule[0].casefold() not in seen_roles:
            seen_roles.add(rule[0].casefold())
            relevant.append(
                IngredientGuidanceItem(
                    ingredient_role=rule[0],
                    examples=ROLE_EXAMPLES[rule[0]],
                    reason=rule[1],
                )
            )

    avoid: list[IngredientGuidanceItem] = []
    seen: set[str] = set()
    for item in profile.get("known_allergies", []):
        if item.casefold() not in seen:
            seen.add(item.casefold())
            avoid.append(
                IngredientGuidanceItem(
                    item=item,
                    reason="Review carefully because this matches a known allergy you reported.",
                )
            )
    for item in profile.get("ingredients_to_avoid", []):
        if item.casefold() not in seen:
            seen.add(item.casefold())
            avoid.append(
                IngredientGuidanceItem(
                    item=item, reason="Avoid based on the ingredient preference you selected."
                )
            )
    if (
        profile.get("fragrance_preference") == "Fragrance-free only"
        and "added fragrance" not in seen
    ):
        avoid.append(
            IngredientGuidanceItem(
                item="Added fragrance", reason="Avoid based on your fragrance-free preference."
            )
        )
    return IngredientGuidance(potentially_relevant=relevant, avoid_or_review=avoid)
