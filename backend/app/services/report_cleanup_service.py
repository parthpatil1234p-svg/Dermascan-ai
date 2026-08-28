import logging
from datetime import datetime, timedelta, timezone

from app.core.config import Settings
from app.utils.file_utils import delete_file_safely, secure_child_path

logger = logging.getLogger(__name__)


def cleanup_expired_report_exports(settings: Settings, *, now: datetime | None = None) -> int:
    current = now or datetime.now(timezone.utc)
    cutoff = current - timedelta(minutes=settings.report_export_expiry_minutes)
    root = settings.report_export_path
    if not root.exists():
        return 0
    removed = 0
    for candidate in root.glob("*"):
        if not candidate.is_file() or candidate.suffix.lower() not in {".pdf", ".tmp"}:
            continue
        try:
            safe = secure_child_path(root, candidate.name)
            modified = datetime.fromtimestamp(safe.stat().st_mtime, tz=timezone.utc)
        except (OSError, ValueError):
            continue
        if modified <= cutoff and delete_file_safely(safe):
            removed += 1
    if removed:
        logger.info("Expired report exports cleaned: %s", removed)
    return removed
