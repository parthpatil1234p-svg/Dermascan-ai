from collections import Counter

from app.core.config import Settings
from app.rules.category_rules import CATEGORY_ORDER
from app.schemas.product_recommendation import StoredRecommendation
from app.services.recommendation_diversity_service import select_diverse_category_candidates


def recommendation_sort_key(item: StoredRecommendation) -> tuple:
    freshness = item.data_freshness
    return (
        -item.final_score,
        len(item.caution_factors),
        -item.score_breakdown.data_quality,
        freshness.availability != "fresh",
        freshness.price != "fresh",
        -item.score_breakdown.visible_concern_match,
        -item.score_breakdown.budget_fit,
        item.product_name.casefold(),
        item.product_id,
    )


def sort_candidates(candidates: list[StoredRecommendation]) -> list[StoredRecommendation]:
    return sorted(candidates, key=recommendation_sort_key)


def select_recommendations(
    candidates: list[StoredRecommendation],
    settings: Settings,
) -> list[StoredRecommendation]:
    qualifying = [
        item for item in candidates if item.final_score >= settings.recommendation_min_display_score
    ]
    grouped = {
        category: sort_candidates([item for item in qualifying if item.category == category])
        for category in CATEGORY_ORDER
    }
    brand_counts: Counter = Counter()
    selected: list[StoredRecommendation] = []
    for category in CATEGORY_ORDER:
        chosen = select_diverse_category_candidates(grouped[category], brand_counts, settings)
        selected.extend(
            item.model_copy(update={"rank_within_category": index})
            for index, item in enumerate(chosen, start=1)
        )
    ordered = sort_candidates(selected)
    ranks = {item.product_id: index for index, item in enumerate(ordered, start=1)}
    return [item.model_copy(update={"overall_rank": ranks[item.product_id]}) for item in selected]
