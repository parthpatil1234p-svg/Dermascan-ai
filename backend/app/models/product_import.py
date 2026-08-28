from datetime import datetime
from typing import Any
from uuid import uuid4


def build_import_job(source_filename: str, source_type: str, now: datetime) -> dict[str, Any]:
    return {
        "import_job_id": f"IMP-{uuid4().hex.upper()}",
        "source_filename": source_filename,
        "source_type": source_type,
        "status": "validating",
        "total_records": 0,
        "valid_records": 0,
        "invalid_records": 0,
        "duplicate_records": 0,
        "inserted_records": 0,
        "updated_records": 0,
        "errors": [],
        "created_at": now,
        "completed_at": None,
    }
