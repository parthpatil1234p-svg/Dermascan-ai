import html
import re
from typing import Any

CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
TEXT_FIELDS = (
    "comment",
    "irritation_description",
    "morning_routine_feedback",
    "night_routine_feedback",
    "export_experience",
)


class FeedbackTextError(ValueError):
    pass


def sanitize_feedback_text(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    cleaned = CONTROL_CHARACTERS.sub("", value).strip()
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        raise FeedbackTextError(f"Feedback comments must not exceed {max_length} characters.")
    return html.escape(cleaned, quote=True)


def sanitize_feedback_fields(payload: Any, max_length: int) -> dict[str, str | None]:
    return {
        name: sanitize_feedback_text(getattr(payload, name, None), max_length)
        for name in TEXT_FIELDS
    }


def analytics_safe_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    forbidden = {"email", "full_name", "comment", "raw_comments", "user_id", "allergies"}
    return {key: value for key, value in snapshot.items() if key not in forbidden}
