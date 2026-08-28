from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.api.dependencies import get_current_user, get_final_reports_collection
from app.core.config import Settings, get_settings
from app.schemas.final_report import PdfExportRequest
from app.schemas.user import UserPublic
from app.services.final_report_service import (
    FinalReportArchivedError,
    FinalReportNotFoundError,
    get_owned_final_report,
)
from app.services.report_export_service import ReportExportError, create_pdf_export
from app.utils.file_utils import delete_file_safely

router = APIRouter(prefix="/final-reports", tags=["report exports"])


@router.post("/{final_report_id}/export/pdf", response_class=FileResponse)
async def export_final_report_pdf(
    final_report_id: str,
    request: PdfExportRequest,
    current_user: UserPublic = Depends(get_current_user),
    reports=Depends(get_final_reports_collection),
    settings: Settings = Depends(get_settings),
):
    try:
        document = await get_owned_final_report(reports, final_report_id, current_user.id)
        exported = create_pdf_export(document, request.privacy_mode, settings)
        await reports.update_one(
            {"_id": document["_id"]},
            {
                "$set": {
                    "export_status": "completed",
                    "last_exported_at": datetime.now(timezone.utc),
                }
            },
        )
        return FileResponse(
            path=exported.physical_path,
            media_type="application/pdf",
            filename=exported.download_filename,
            background=BackgroundTask(delete_file_safely, exported.physical_path),
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )
    except (FinalReportNotFoundError, FinalReportArchivedError) as error:
        raise HTTPException(status_code=404, detail="Final report not found.") from error
    except ReportExportError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500, detail="We could not safely export this report as a PDF."
        ) from error
