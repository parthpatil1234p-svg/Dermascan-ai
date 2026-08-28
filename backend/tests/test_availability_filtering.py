from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.services.availability_filter_service import evaluate_availability
from tests.eligibility_fixtures import real_product


def test_available_country_is_positive():
    hard, cautions, positives, gaps = evaluate_availability(real_product(), "IN", get_settings())
    assert hard == cautions == gaps == []
    assert positives[0].code == "AVAILABLE_IN_USER_COUNTRY"


def test_limited_availability_adds_caution():
    hard, cautions, _, gaps = evaluate_availability(
        real_product(availability_status="limited"), "IN", get_settings()
    )
    assert hard == gaps == []
    assert cautions[0].code == "LIMITED_AVAILABILITY"


def test_unavailable_status_excludes_product():
    hard, _, _, _ = evaluate_availability(
        real_product(availability_status="unavailable"), "IN", get_settings()
    )
    assert hard[0].code == "UNAVAILABLE_IN_USER_COUNTRY"


def test_country_not_listed_excludes_product():
    hard, _, _, _ = evaluate_availability(real_product(country_codes=["GB"]), "IN", get_settings())
    assert hard[0].code == "UNAVAILABLE_IN_USER_COUNTRY"


def test_unknown_availability_is_information_gap():
    hard, _, _, gaps = evaluate_availability(
        real_product(availability_status="unknown", availability_checked_at=None),
        "IN",
        get_settings(),
    )
    assert hard == []
    assert gaps[0].code == "AVAILABILITY_UNKNOWN"


def test_stale_availability_adds_caution():
    old = datetime.now(timezone.utc) - timedelta(days=30)
    _, cautions, _, _ = evaluate_availability(
        real_product(availability_checked_at=old), "IN", get_settings()
    )
    assert cautions[0].code == "AVAILABILITY_DATA_STALE"
