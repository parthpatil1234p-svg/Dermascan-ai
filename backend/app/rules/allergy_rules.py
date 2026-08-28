ALLERGY_ALIASES = {
    "fragrance": "added_fragrance",
    "perfume": "added_fragrance",
    "parfum": "added_fragrance",
    "added fragrance": "added_fragrance",
    "synthetic fragrance": "added_fragrance",
    "essential oil": "essential_oil",
    "essential oils": "essential_oil",
    "drying alcohol": "drying_alcohol",
    "benzoyl peroxide": "benzoyl_peroxide",
    "retinoid": "retinoid",
    "retinol": "retinoid",
}

ALLERGY_PRODUCT_FLAGS = {
    "added_fragrance": {"contains_added_fragrance"},
    "essential_oil": {"contains_essential_oils"},
    "drying_alcohol": {"contains_drying_alcohol"},
    "benzoyl_peroxide": {"contains_benzoyl_peroxide"},
    "retinoid": {"contains_retinoid"},
}
