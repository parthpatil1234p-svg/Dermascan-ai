from app.schemas.product_recommendation import (
    RecommendationCandidate,
    RecommendationConfidence,
    RecommendationContext,
    RecommendationFreshness,
    RecommendationScoreBreakdown,
    StoredRecommendation,
)


def confidence_label(score: float) -> RecommendationConfidence:
    if score >= 80:
        return "high"
    if score >= 60:
        return "moderate"
    return "low"


def calculate_recommendation_confidence(
    candidate: RecommendationCandidate,
    context: RecommendationContext,
    breakdown: RecommendationScoreBreakdown,
    freshness: RecommendationFreshness,
    *,
    score_gap: float,
) -> tuple[RecommendationConfidence, list[str]]:
    score = 20.0
    reasons = ["The required skin profile fields were complete."]
    if context.skin_type.status == "estimated":
        score += context.skin_type.confidence * 20.0
        reasons.append("The broad skin-type estimate was available with recorded confidence.")
    else:
        score += 7.0
        reasons.append("The broad skin-type estimate was uncertain.")
    if any(status in {"observed", "possible"} for status in context.concerns.values()):
        score += 15.0
        reasons.append("Visible skincare observations were available for relevance matching.")
    else:
        score += 7.0
        reasons.append("Few visible skincare observations were available for matching.")
    score += breakdown.data_quality * 0.20
    if breakdown.data_quality >= 80:
        reasons.append("The product record had comparatively complete catalogue data.")
    else:
        reasons.append("The product record had catalogue quality limitations.")
    caution_count = len(candidate.cautions)
    score += max(0.0, 15.0 - caution_count * 4.0)
    if caution_count:
        reasons.append(f"The eligibility report contained {caution_count} caution factor(s).")
    freshness_values = freshness.model_dump().values()
    fresh_count = sum(value == "fresh" for value in freshness_values)
    score += fresh_count / 3.0 * 10.0
    if fresh_count < 3:
        reasons.append("Some price, availability, or source information was not fresh.")
    score += min(max(score_gap, 0.0), 10.0)
    if score_gap >= 5:
        reasons.append("The score was meaningfully separated from the next nearby candidate.")
    return confidence_label(score), reasons


def calculate_overall_confidence(
    recommendations: list[StoredRecommendation],
    context: RecommendationContext,
) -> tuple[RecommendationConfidence, list[str]]:
    if not recommendations:
        return "low", ["No candidate met the configured minimum display score."]
    numeric = {"high": 3, "moderate": 2, "low": 1}
    average = sum(numeric[item.recommendation_confidence] for item in recommendations) / len(
        recommendations
    )
    label: RecommendationConfidence = (
        "high" if average >= 2.6 else "moderate" if average >= 1.6 else "low"
    )
    reasons = [f"{len(recommendations)} catalogue option(s) met the configured display threshold."]
    if context.skin_type.status == "uncertain":
        if label == "high":
            label = "moderate"
        reasons.append("Skin-type uncertainty reduced recommendation confidence.")
    if any(item.caution_factors for item in recommendations):
        reasons.append("Some selected options retain visible caution factors.")
    else:
        reasons.append("Selected options had no recorded eligibility cautions.")
    return label, reasons
