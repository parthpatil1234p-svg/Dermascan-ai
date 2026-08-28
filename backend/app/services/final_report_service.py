from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from app.models.final_report import (
    build_final_report_document,
    final_report_list_item,
)
from app.repositories.final_report_repository import (
    archive_report,
    find_all_for_upload,
    find_latest_owned_report,
    find_owned_final_report,
    insert_final_report,
    supersede_report,
)
from app.schemas.final_report import (
    FinalReportArchiveResponse,
    FinalReportListResponse,
)
from app.schemas.pagination import pagination_metadata
from app.services.report_aggregation_service import (
    aggregate_sections,
    analysis_mode,
    load_source_reports,
    source_metadata,
)
from app.services.report_summary_service import generate_executive_summary
from app.services.report_validation_service import (
    ReportRelationshipError,
    determine_report_status,
    missing_required_sources,
    validate_source_relationships,
)
from app.services.report_version_service import (
    generate_public_report_id,
    next_report_version,
    source_fingerprint,
)
from app.services.upload_service import get_owned_upload_document


class FinalReportNotFoundError(Exception):
    pass


class FinalReportArchivedError(Exception):
    pass


class FinalReportGenerationConflictError(Exception):
    pass


class FinalReportGenerationError(Exception):
    pass


async def _set_upload_status(
    uploads: Any, upload: dict[str, Any], status: str, now: datetime
) -> None:
    await uploads.update_one(
        {"_id": upload["_id"]}, {"$set": {"status": status, "updated_at": now}}
    )


async def generate_owned_final_report(
    *,
    upload_id: str,
    user_id: str,
    collections: dict[str, Any],
    force_new_version: bool = False,
) -> dict[str, Any]:
    uploads = collections["image_upload"]
    upload = await get_owned_upload_document(uploads, upload_id, user_id)
    if upload is None:
        raise FinalReportNotFoundError
    if upload.get("status") == "final_report_generating":
        raise FinalReportGenerationConflictError("Final report generation is already running.")
    now = datetime.now(timezone.utc)
    await _set_upload_status(uploads, upload, "final_report_generating", now)
    try:
        sources = await load_source_reports(
            upload_id=upload_id, user_id=user_id, collections=collections
        )
        validate_source_relationships(sources, user_id, upload_id)
        missing = missing_required_sources(sources)
        status, limitations = determine_report_status(sources, missing)
        sections = await aggregate_sections(sources, collections["products"])
        ids, versions, model_versions, engine_versions = source_metadata(sources)
        fingerprint = source_fingerprint(ids, versions)
        existing_reports = await find_all_for_upload(
            collections["final_reports"], upload_id, user_id
        )
        active = next(
            (
                item
                for item in existing_reports
                if item.get("report_status") != "superseded" and not item.get("is_archived")
            ),
            None,
        )
        if active and not force_new_version and active.get("source_fingerprint") == fingerprint:
            await _set_upload_status(
                uploads,
                upload,
                (
                    "workflow_completed"
                    if active["report_status"] != "incomplete"
                    else "final_report_incomplete"
                ),
                now,
            )
            return active
        report_id = generate_public_report_id(now)
        profile = sources.get("skin_profile")
        skin = sources.get("skin_type")
        concerns = sources.get("skin_concern")
        summary = generate_executive_summary(skin, concerns, profile, incomplete=bool(missing))
        document = build_final_report_document(
            final_report_id=report_id,
            user_id=user_id,
            upload_id=upload_id,
            report_version=next_report_version(existing_reports),
            report_status=status,
            source_report_ids=ids,
            source_versions=versions,
            source_fingerprint=fingerprint,
            summary=summary,
            sections=sections,
            limitations=limitations,
            model_versions=model_versions,
            engine_versions=engine_versions,
            analysis_mode=analysis_mode(sources),
            analysis_date=upload.get("created_at", now),
            now=now,
            supersedes_report_id=active.get("final_report_id") if active else None,
        )
        await insert_final_report(collections["final_reports"], document)
        if active:
            await supersede_report(collections["final_reports"], active, report_id, now)
        final_status = (
            "final_report_incomplete"
            if status == "incomplete"
            else (
                "final_report_completed_with_limitations"
                if status == "complete_with_limitations"
                else "final_report_completed"
            )
        )
        await _set_upload_status(uploads, upload, final_status, now)
        if status != "incomplete":
            await _set_upload_status(uploads, upload, "workflow_completed", now)
        return document
    except (ReportRelationshipError, FinalReportGenerationConflictError):
        await _set_upload_status(uploads, upload, "final_report_failed", datetime.now(timezone.utc))
        raise
    except Exception as exc:
        await _set_upload_status(uploads, upload, "final_report_failed", datetime.now(timezone.utc))
        raise FinalReportGenerationError from exc


async def get_owned_final_report(
    collection: Any, final_report_id: str, user_id: str
) -> dict[str, Any]:
    document = await find_owned_final_report(collection, final_report_id, user_id)
    if document is None:
        raise FinalReportNotFoundError
    if document.get("is_archived"):
        raise FinalReportArchivedError
    return document


async def get_latest_report(
    collection: Any, uploads: Any, upload_id: str, user_id: str
) -> dict[str, Any]:
    if await get_owned_upload_document(uploads, upload_id, user_id) is None:
        raise FinalReportNotFoundError
    document = await find_latest_owned_report(collection, upload_id, user_id)
    if document is None:
        raise FinalReportNotFoundError
    return document


async def list_owned_reports(
    collection: Any,
    user_id: str,
    *,
    page: int,
    page_size: int,
    report_status: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
    sort: str,
) -> FinalReportListResponse:
    query: dict[str, Any] = {"user_id": ObjectId(user_id), "is_archived": False}
    if report_status:
        query["report_status"] = report_status
    if date_from or date_to:
        query["generated_at"] = {}
        if date_from:
            query["generated_at"]["$gte"] = date_from
        if date_to:
            query["generated_at"]["$lte"] = date_to
    total = await collection.count_documents(query)
    direction = 1 if sort == "oldest" else -1
    documents = (
        await collection.find(query)
        .sort("generated_at", direction)
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list(length=page_size)
    )
    return FinalReportListResponse(
        reports=[final_report_list_item(item) for item in documents],
        pagination=pagination_metadata(page, page_size, total),
    )


async def archive_owned_final_report(
    collection: Any, final_report_id: str, user_id: str
) -> FinalReportArchiveResponse:
    document = await find_owned_final_report(collection, final_report_id, user_id)
    if document is None:
        raise FinalReportNotFoundError
    now = datetime.now(timezone.utc)
    await archive_report(collection, document, now)
    return FinalReportArchiveResponse(
        final_report_id=final_report_id,
        is_archived=True,
        archived_at=now,
        message="The report was archived. Its dependent analysis records were not deleted.",
    )
