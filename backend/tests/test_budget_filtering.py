from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.schemas.product_eligibility import FilteringBudget
from app.services.budget_filter_service import evaluate_budget
from tests.eligibility_fixtures import real_product


def evaluate(price, budget, **product_overrides):
    product = real_product(price=price, **product_overrides)
    return evaluate_budget(product, budget, get_settings())


def test_price_within_strict_budget_is_positive():
    result = evaluate(
        {"amount": 500, "currency": "INR"},
        FilteringBudget(minimum=200, maximum=1000, mandatory=True),
    )
    assert result[2][0].code == "PRICE_WITHIN_BUDGET"


def test_price_equal_to_maximum_is_allowed_with_near_limit_caution():
    hard, cautions, _, _ = evaluate(
        {"amount": 1000, "currency": "INR"},
        FilteringBudget(minimum=200, maximum=1000, mandatory=True),
    )
    assert hard == []
    assert cautions[0].code == "PRICE_NEAR_BUDGET_LIMIT"


def test_strict_budget_excludes_above_maximum():
    hard, _, _, _ = evaluate(
        {"amount": 1001, "currency": "INR"},
        FilteringBudget(minimum=200, maximum=1000, mandatory=True),
    )
    assert hard[0].code == "PRICE_ABOVE_BUDGET"


def test_flexible_budget_keeps_ten_percent_overage_as_caution():
    hard, cautions, _, _ = evaluate(
        {"amount": 1050, "currency": "INR"},
        FilteringBudget(minimum=200, maximum=1000, mandatory=False),
    )
    assert hard == []
    assert cautions[0].code == "PRICE_NEAR_BUDGET_LIMIT"


def test_flexible_budget_excludes_beyond_configured_tolerance():
    hard, _, _, _ = evaluate(
        {"amount": 1200, "currency": "INR"},
        FilteringBudget(minimum=200, maximum=1000, mandatory=False),
    )
    assert hard[0].code == "PRICE_ABOVE_BUDGET"


def test_missing_price_with_strict_budget_is_information_gap():
    hard, cautions, positives, gaps = evaluate_budget(
        real_product(price=None, price_checked_at=None),
        FilteringBudget(minimum=200, maximum=1000, mandatory=True),
        get_settings(),
    )
    assert hard == cautions == positives == []
    assert gaps[0].code == "PRICE_UNKNOWN"


def test_unsupported_currency_is_not_converted():
    _, _, _, gaps = evaluate(
        {"amount": 10, "currency": "USD"}, FilteringBudget(minimum=1, maximum=1000, mandatory=True)
    )
    assert gaps[0].code == "PRICE_UNKNOWN"


def test_stale_price_adds_caution():
    old = datetime.now(timezone.utc) - timedelta(days=60)
    _, cautions, _, _ = evaluate(
        {"amount": 500, "currency": "INR"},
        FilteringBudget(minimum=200, maximum=1000, mandatory=True),
        price_checked_at=old,
    )
    assert "PRICE_DATA_STALE" in {item.code for item in cautions}


def test_no_budget_does_not_claim_price_within_selected_budget():
    _, _, positives, _ = evaluate(
        {"amount": 500, "currency": "INR"},
        FilteringBudget(minimum=None, maximum=None, mandatory=False),
    )
    assert positives == []
