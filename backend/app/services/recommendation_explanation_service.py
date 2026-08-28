from app.schemas.product_recommendation import (
    AppliedPenalty,
    RecommendationCandidate,
    RecommendationContext,
    RecommendationScoreBreakdown,
)


def build_recommendation_explanation(
    candidate: RecommendationCandidate,
    context: RecommendationContext,
    breakdown: RecommendationScoreBreakdown,
    penalties: list[AppliedPenalty],
    band: str,
) -> tuple[str, list[str], list[str]]:
    positives: list[str] = []
    if breakdown.skin_type_match >= 85:
        positives.append(
            "Broad skin-type compatibility is documented."
            if context.skin_type.status == "uncertain"
            else f"Catalogued for {context.skin_type.value} skin."
        )
    matched_concerns = sorted(
        code
        for code, status in context.concerns.items()
        if status in {"observed", "possible"} and code in candidate.target_visible_concerns
    )
    if matched_concerns:
        positives.append(
            "Mapped to visible skincare goals: "
            + ", ".join(code.replace("_", " ") for code in matched_concerns)
            + "."
        )
    if breakdown.ingredient_relevance >= 65 and candidate.highlighted_ingredients:
        positives.append(
            "Relevant catalogue ingredients include "
            + ", ".join(candidate.highlighted_ingredients[:3])
            + "."
        )
    if breakdown.budget_fit >= 65:
        positives.append("Fits the selected budget context.")
    if breakdown.availability >= 60:
        positives.append(f"Marked {candidate.availability_status} in the selected country.")
    if breakdown.sensitivity_compatibility >= 90:
        positives.append("Catalogue sensitivity information is comparatively favourable.")
    if not positives:
        positives.append("Meets the minimum project-specific catalogue relevance threshold.")

    cautions = list(dict.fromkeys(reason.message for reason in candidate.cautions))
    for penalty in penalties:
        if penalty.message not in cautions:
            cautions.append(penalty.message)
    why = (
        f"This {candidate.category.replace('_', ' ')} is a {band.lower()} catalogue match because "
        + " ".join(positives[:3])
    )
    return why, positives, cautions


def explanation_uses_candidate_evidence(
    explanation: str,
    candidate: RecommendationCandidate,
) -> bool:
    text = explanation.casefold()
    supported = {
        candidate.category.replace("_", " ").casefold(),
        *(value.casefold() for value in candidate.highlighted_ingredients),
        *(value.replace("_", " ").casefold() for value in candidate.target_visible_concerns),
    }
    return any(value and value in text for value in supported)
