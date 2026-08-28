from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import Settings, get_settings
from app.database.mongodb import mongo_connection
from app.services.face_crop_service import cleanup_expired_face_crops
from app.services.image_preprocessing_service import cleanup_expired_preprocessed_images
from app.services.report_cleanup_service import cleanup_expired_report_exports
from app.services.upload_service import cleanup_expired_uploads


async def _count(cursor: Any) -> int:
    count = 0
    async for _ in cursor:
        count += 1
    return count


def _expired_export_count(settings: Settings, now: datetime) -> int:
    root = settings.report_export_path
    if not root.exists():
        return 0
    cutoff = now - timedelta(minutes=settings.report_export_expiry_minutes)
    count = 0
    for candidate in root.glob("*"):
        if not candidate.is_file() or candidate.suffix.lower() not in {".pdf", ".tmp"}:
            continue
        try:
            modified = datetime.fromtimestamp(candidate.stat().st_mtime, tz=timezone.utc)
            candidate.resolve().relative_to(root.resolve())
        except (OSError, ValueError):
            continue
        if modified <= cutoff:
            count += 1
    return count


async def cleanup(*, dry_run: bool) -> dict[str, int | bool]:
    settings = get_settings()
    database = await mongo_connection.connect(settings)
    now = datetime.now(timezone.utc)
    try:
        if dry_run:
            uploads = await _count(
                database["image_uploads"].find(
                    {"expires_at": {"$lte": now}, "status": {"$ne": "expired"}}
                )
            )
            crops = await _count(
                database["face_detection_reports"].find({"expires_at": {"$lte": now}})
            )
            preprocessed = await _count(
                database["image_preprocessing_reports"].find(
                    {
                        "expires_at": {"$lte": now},
                        "preprocessing_status": {"$ne": "expired"},
                    }
                )
            )
            exports = _expired_export_count(settings, now)
        else:
            uploads = await cleanup_expired_uploads(
                database["image_uploads"],
                settings,
                database["image_quality_reports"],
                database["face_detection_reports"],
                database["image_preprocessing_reports"],
                database["skin_type_reports"],
                database["skin_concern_reports"],
            )
            crops = await cleanup_expired_face_crops(database["face_detection_reports"], settings)
            preprocessed = await cleanup_expired_preprocessed_images(
                database["image_preprocessing_reports"], settings
            )
            exports = cleanup_expired_report_exports(settings, now=now)
        return {
            "dry_run": dry_run,
            "expired_uploads": uploads,
            "expired_face_crops": crops,
            "expired_preprocessed_images": preprocessed,
            "expired_report_exports": exports,
        }
    finally:
        await mongo_connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean expired DermaScan temporary files and matching records."
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(cleanup(dry_run=args.dry_run)), indent=2))


if __name__ == "__main__":
    main()
