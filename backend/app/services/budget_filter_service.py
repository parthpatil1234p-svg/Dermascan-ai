from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import Settings
from app.rules.budget_rules import NEAR_BUDGET_RATIO
from app.schemas.product_eligibility import EligibilityReason, FilteringBudget


def evaluate_budget(
    product: dict[str, Any],
    budget: FilteringBudget,
    settings: Settings,
) -> tuple[
    list[EligibilityReason],
    list[EligibilityReason],
    list[EligibilityReason],
    list[EligibilityReason],
]:
    exclusions: list[EligibilityReason] = []
    cautions: list[EligibilityReason] = []
    positives: list[EligibilityReason] = []
    gaps: list[EligibilityReason] = []
    price = product.get("price")
    if not price:
        reason = EligibilityReason(
            code="PRICE_UNKNOWN", message="A current product price is not available."
        )
        (gaps if budget.mandatory else cautions).append(reason)
        return exclusions, cautions, positives, gaps
    if price.get("currency") != budget.currency:
        gaps.append(
            EligibilityReason(
                code="PRICE_UNKNOWN",
                message="The catalogue price uses an unsupported currency, so no conversion was guessed.",
                matched_value=price.get("currency"),
            )
        )
        return exclusions, cautions, positives, gaps
    amount = float(price["amount"])
    minimum, maximum = budget.minimum, budget.maximum
    if minimum is None and maximum is None:
        pass
    elif budget.mandatory and minimum is not None and amount < minimum:
        exclusions.append(
            EligibilityReason(
                code="PRICE_ABOVE_BUDGET",
                message="This product falls outside the mandatory price range you selected.",
                matched_value=f"INR {amount:g}",
            )
        )
    elif maximum is not None and amount > maximum:
        flexible_limit = maximum * (1 + settings.budget_soft_overage_percent / 100)
        if not budget.mandatory and amount <= flexible_limit:
            cautions.append(
                EligibilityReason(
                    code="PRICE_NEAR_BUDGET_LIMIT",
                    message="This product is slightly above your preferred budget and may receive a lower ranking later.",
                    matched_value=f"INR {amount:g}",
                )
            )
        else:
            exclusions.append(
                EligibilityReason(
                    code="PRICE_ABOVE_BUDGET",
                    message="This product is above the maximum budget you selected.",
                    matched_value=f"INR {amount:g}",
                )
            )
    elif maximum is not None and amount >= maximum * NEAR_BUDGET_RATIO:
        cautions.append(
            EligibilityReason(
                code="PRICE_NEAR_BUDGET_LIMIT",
                message="This product is near the top of your selected budget.",
                matched_value=f"INR {amount:g}",
            )
        )
    elif minimum is not None or maximum is not None:
        positives.append(
            EligibilityReason(
                code="PRICE_WITHIN_BUDGET",
                message="The catalogue price is within your selected budget.",
            )
        )
    checked = product.get("price_checked_at")
    if checked is None or checked < datetime.now(timezone.utc) - timedelta(
        days=settings.product_price_stale_days
    ):
        cautions.append(
            EligibilityReason(
                code="PRICE_DATA_STALE",
                message="The displayed price may be outdated. Confirm the current price before purchasing.",
            )
        )
    return exclusions, cautions, positives, gaps
