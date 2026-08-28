from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import Settings
from app.schemas.product_eligibility import EligibilityReason


def evaluate_availability(product: dict[str, Any], country: str, settings: Settings):
    exclusions: list[EligibilityReason] = []
    cautions: list[EligibilityReason] = []
    positives: list[EligibilityReason] = []
    gaps: list[EligibilityReason] = []
    countries = set(product.get("country_codes", []))
    status = product.get("availability_status", "unknown")
    if status == "unknown" or not countries:
        gaps.append(
            EligibilityReason(
                code="AVAILABILITY_UNKNOWN",
                message="Availability in your selected country could not be confirmed.",
            )
        )
    elif country not in countries or status == "unavailable":
        exclusions.append(
            EligibilityReason(
                code="UNAVAILABLE_IN_USER_COUNTRY",
                message="This product is not catalogued as available in your selected country.",
                matched_value=country,
            )
        )
    elif status == "limited":
        cautions.append(
            EligibilityReason(
                code="LIMITED_AVAILABILITY",
                message="Catalogue availability in your country is limited.",
                matched_value=country,
            )
        )
    else:
        positives.append(
            EligibilityReason(
                code="AVAILABLE_IN_USER_COUNTRY",
                message="The product is catalogued as available in your selected country.",
                matched_value=country,
            )
        )
    checked = product.get("availability_checked_at")
    if checked is None or checked < datetime.now(timezone.utc) - timedelta(
        days=settings.product_availability_stale_days
    ):
        cautions.append(
            EligibilityReason(
                code="AVAILABILITY_DATA_STALE",
                message="Availability information may be outdated and should be confirmed.",
            )
        )
    return exclusions, cautions, positives, gaps
