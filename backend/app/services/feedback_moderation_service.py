import re

SCRIPT_PATTERN = re.compile(r"<\s*(script|iframe|object)|javascript:", re.IGNORECASE)
CONTACT_PATTERN = re.compile(r"(?:[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?:\+?\d[\d\s-]{8,}\d))")
REPEATED_PATTERN = re.compile(r"(.)\1{14,}", re.IGNORECASE)
UNSUPPORTED_CLAIM_PATTERN = re.compile(
    r"\b(?:this proves|definitely diagnosed|guaranteed cure|medically proven by this app)\b",
    re.IGNORECASE,
)


def assess_feedback_moderation(text_values: list[str | None]) -> tuple[str, list[str]]:
    text = " ".join(value for value in text_values if value)
    reasons: list[str] = []
    if SCRIPT_PATTERN.search(text):
        reasons.append("POTENTIAL_SCRIPT_INJECTION")
    if CONTACT_PATTERN.search(text):
        reasons.append("PERSONAL_CONTACT_INFORMATION")
    if REPEATED_PATTERN.search(text):
        reasons.append("EXCESSIVE_REPEATED_CONTENT")
    if UNSUPPORTED_CLAIM_PATTERN.search(text):
        reasons.append("UNSUPPORTED_MEDICAL_CLAIM")
    return ("flagged", reasons) if reasons else ("clear", [])
