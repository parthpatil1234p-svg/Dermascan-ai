from collections import Counter

from app.core.config import Settings
from app.schemas.product_recommendation import StoredRecommendation


def select_diverse_category_candidates(
    candidates: list[StoredRecommendation],
    brand_counts: Counter,
    settings: Settings,
) -> list[StoredRecommendation]:
    selected: list[StoredRecommendation] = []
    used_profiles: set[tuple[str, ...]] = set()
    used_tiers: set[str] = set()
    remaining = list(candidates)
    while remaining and len(selected) < settings.recommendation_max_per_category:
        viable = [
            item
            for item in remaining
            if brand_counts[item.normalized_brand_name] < settings.recommendation_max_same_brand
            and tuple(item.ingredient_profile) not in used_profiles
        ]
        if not viable:
            break
        diverse_tier = [item for item in viable if item.price_tier not in used_tiers]
        chosen = (diverse_tier or viable)[0]
        selected.append(chosen)
        brand_counts[chosen.normalized_brand_name] += 1
        used_profiles.add(tuple(chosen.ingredient_profile))
        used_tiers.add(chosen.price_tier)
        remaining.remove(chosen)
    return selected
