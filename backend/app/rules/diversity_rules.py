PRICE_TIER_LOW_MAX = 500
PRICE_TIER_MID_MAX = 1000


def price_tier(price: dict | None) -> str:
    if not price:
        return "unknown"
    amount = float(price["amount"])
    if amount <= PRICE_TIER_LOW_MAX:
        return "value"
    if amount <= PRICE_TIER_MID_MAX:
        return "mid"
    return "upper"
