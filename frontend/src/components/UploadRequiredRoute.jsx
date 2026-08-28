import { useEffect, useRef } from "react";
import { Navigate } from "react-router-dom";
import { ROUTES } from "../constants/appContent";
import { useUpload } from "../context/UploadContext";

const AVAILABLE_UPLOAD_STATUSES = new Set([
  "validated",
  "quality_passed",
  "quality_warning",
  "quality_failed",
  "face_detection_pending",
  "face_detecting",
  "face_detected",
  "face_detection_warning",
  "face_detection_failed",
  "preprocessing_pending",
  "preprocessing",
  "preprocessing_completed",
  "preprocessing_warning",
  "preprocessing_failed",
  "skin_type_analysis_pending",
  "skin_type_analyzing",
  "skin_type_estimated",
  "skin_type_uncertain",
  "skin_type_analysis_failed",
  "skin_concern_analysis_pending",
  "skin_concern_analyzing",
  "skin_concern_analysis_completed",
  "skin_concern_analysis_uncertain",
  "skin_concern_analysis_failed",
  "product_discovery_pending",
  "product_eligibility_pending",
  "product_eligibility_evaluating",
  "product_eligibility_completed",
  "product_eligibility_completed_with_gaps",
  "product_eligibility_failed",
  "recommendation_scoring_pending",
  "recommendation_scoring",
  "recommendations_completed",
  "recommendations_completed_with_limitations",
  "recommendations_failed",
  "routine_generation_pending",
  "routine_generating",
  "routine_completed",
  "routine_completed_with_limitations",
  "routine_generation_failed",
  "final_report_pending",
  "final_report_generating",
  "final_report_completed",
  "final_report_completed_with_limitations",
  "final_report_incomplete",
  "final_report_failed",
  "workflow_completed",
]);

export default function UploadRequiredRoute({ children }) {
  const requestedUploadId = useRef("");
  const {
    uploadId,
    uploadStatus,
    isVerified,
    isVerifying,
    verificationError,
    verifyCurrentUpload,
  } = useUpload();

  useEffect(() => {
    if (uploadId && !isVerified && requestedUploadId.current !== uploadId) {
      requestedUploadId.current = uploadId;
      verifyCurrentUpload().catch(() => {});
    }
  }, [uploadId, isVerified, verifyCurrentUpload]);

  if (!uploadId) {
    return <Navigate to={ROUTES.faceScan} replace />;
  }

  if (isVerifying || (!isVerified && !verificationError)) {
    return (
      <section className="flex min-h-[55vh] items-center justify-center px-4">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
          <p className="mt-4 text-sm font-semibold text-slate-700">
            Confirming your temporary upload...
          </p>
        </div>
      </section>
    );
  }

  if (verificationError || !AVAILABLE_UPLOAD_STATUSES.has(uploadStatus)) {
    return (
      <Navigate
        to={ROUTES.faceScan}
        replace
        state={{ uploadError: "Select and upload a valid facial image to continue." }}
      />
    );
  }

  return children;
}
