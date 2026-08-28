import secrets
from datetime import datetime
from typing import Any

REPORT_GENERATOR_VERSION = "1.0.0"


def generate_public_report_id(now: datetime) -> str:
    return f"DSR-{now.year}-{secrets.token_hex(4).upper()}"


def next_report_version(existing_reports: list[dict[str, Any]]) -> int:
    return max((int(item.get("report_version", 0)) for item in existing_reports), default=0) + 1


def source_fingerprint(source_report_ids: dict[str, str], source_versions: dict[str, str]) -> str:
    values = [f"{key}:{source_report_ids[key]}" for key in sorted(source_report_ids)]
    values.extend(f"{key}:{source_versions[key]}" for key in sorted(source_versions))
    return "|".join(values)
