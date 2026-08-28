from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import (
    get_catalogue_review_signals_collection,
    get_feedback_analytics_collection,
    get_feedback_collection,
    get_feedback_moderation_audit_collection,
    require_admin,
)
from app.core.config import Settings, get_settings
from app.models.feedback import feedback_document_to_response
from app.schemas.feedback import CatalogueReviewUpdate, ModerationRequest
from app.schemas.user import UserPublic
from app.services.feedback_analytics_service import create_analytics_snapshot

router = APIRouter(prefix="/admin", tags=["feedback administration"])


@router.get("/feedback/analytics")
async def read_feedback_analytics(
    _: UserPublic = Depends(require_admin),
    feedback=Depends(get_feedback_collection),
    snapshots=Depends(get_feedback_analytics_collection),
    settings: Settings = Depends(get_settings),
) -> dict:
    return await create_analytics_snapshot(
        feedback, snapshots, settings.feedback_analytics_min_group_size
    )


@router.get("/feedback")
async def list_feedback_for_review(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    moderation_status: str | None = None,
    _: UserPublic = Depends(require_admin),
    collection=Depends(get_feedback_collection),
) -> dict:
    query = {"moderation_status": moderation_status} if moderation_status else {}
    total = await collection.count_documents(query)
    documents = (
        await collection.find(query)
        .sort("created_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list(length=page_size)
    )
    return {
        "feedback": [
            feedback_document_to_response(item).model_dump(mode="json") for item in documents
        ],
        "page": page,
        "page_size": page_size,
        "total_items": total,
    }


@router.get("/feedback/{feedback_id}")
async def read_feedback_for_review(
    feedback_id: str,
    _: UserPublic = Depends(require_admin),
    collection=Depends(get_feedback_collection),
) -> dict:
    document = await collection.find_one({"feedback_id": feedback_id})
    if document is None:
        raise HTTPException(status_code=404, detail="Feedback not found.")
    return feedback_document_to_response(document).model_dump(mode="json")


@router.patch("/feedback/{feedback_id}/moderate")
async def moderate_feedback(
    feedback_id: str,
    payload: ModerationRequest,
    admin: UserPublic = Depends(require_admin),
    collection=Depends(get_feedback_collection),
    audit=Depends(get_feedback_moderation_audit_collection),
) -> dict:
    document = await collection.find_one({"feedback_id": feedback_id})
    if document is None:
        raise HTTPException(status_code=404, detail="Feedback not found.")
    now = datetime.now(timezone.utc)
    await collection.update_one(
        {"_id": document["_id"]},
        {
            "$set": {
                "moderation_status": payload.moderation_status,
                "feedback_status": payload.feedback_status,
                "updated_at": now,
            }
        },
    )
    await audit.insert_one(
        {
            "feedback_id": feedback_id,
            "admin_user_id": admin.id,
            "action": payload.moderation_status,
            "note": payload.moderation_note.strip(),
            "created_at": now,
        }
    )
    return {"feedback_id": feedback_id, "moderation_status": payload.moderation_status}


@router.get("/catalogue-review-signals")
async def list_catalogue_review_signals(
    review_status: str | None = None,
    _: UserPublic = Depends(require_admin),
    collection=Depends(get_catalogue_review_signals_collection),
) -> dict:
    query = {"review_status": review_status} if review_status else {}
    documents = await collection.find(query).sort("last_reported_at", -1).to_list(length=200)
    return {
        "signals": [
            {key: value for key, value in item.items() if key != "_id"} for item in documents
        ]
    }


@router.patch("/catalogue-review-signals/{signal_id}")
async def update_catalogue_review_signal(
    signal_id: str,
    payload: CatalogueReviewUpdate,
    _: UserPublic = Depends(require_admin),
    collection=Depends(get_catalogue_review_signals_collection),
) -> dict:
    document = await collection.find_one({"signal_id": signal_id})
    if document is None:
        raise HTTPException(status_code=404, detail="Catalogue review signal not found.")
    now = datetime.now(timezone.utc)
    await collection.update_one(
        {"_id": document["_id"]},
        {
            "$set": {
                "review_status": payload.review_status,
                "reviewed_at": now,
                "resolution_notes": (
                    payload.resolution_notes.strip() if payload.resolution_notes else None
                ),
                "updated_at": now,
            }
        },
    )
    return {"signal_id": signal_id, "review_status": payload.review_status}
