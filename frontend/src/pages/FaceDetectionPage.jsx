import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Crop,
  Eye,
  Focus,
  RefreshCcw,
  ScanFace,
  ShieldCheck,
  UploadCloud,
  UserRoundCheck,
  XCircle,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import DisclaimerBox from "../components/DisclaimerBox";
import ErrorMessage from "../components/ErrorMessage";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import { FACE_DETECTION_STAGES, ROUTES } from "../constants/appContent";
import { useFaceDetection } from "../context/FaceDetectionContext";
import { useImageQuality } from "../context/ImageQualityContext";
import { useUpload } from "../context/UploadContext";

const STATUS_DETAILS = {
  passed: {
    label: "Face Detection Successful",
    description: "One suitable face was detected and prepared for preprocessing.",
    icon: CheckCircle2,
    classes: "border-leaf-200 bg-leaf-50 text-leaf-800",
  },
  warning: {
    label: "Usable with Face-Position Warning",
    description: "A face was detected, but a better image is recommended.",
    icon: AlertTriangle,
    classes: "border-amber-200 bg-amber-50 text-amber-900",
  },
  failed: {
    label: "Upload Another Image",
    description: "This image cannot continue to preprocessing.",
    icon: XCircle,
    classes: "border-red-200 bg-red-50 text-red-800",
  },
};

const statusText = (value) =>
  value
    ? value
        .split("_")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ")
    : "Not available";

function DetectionProgress({ progress }) {
  const activeIndex = Math.min(
    FACE_DETECTION_STAGES.length - 1,
    Math.floor((progress / 100) * FACE_DETECTION_STAGES.length),
  );

  return (
    <div className="mx-auto max-w-3xl border-y border-slate-200 py-8" role="status">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-950">
            Detecting a usable facial region
          </h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            The backend is checking face count, position, size, and crop readiness.
          </p>
        </div>
        <span className="text-lg font-bold text-brand-700">{progress}%</span>
      </div>
      <div
        className="mt-5 h-2 overflow-hidden rounded-full bg-slate-200"
        role="progressbar"
        aria-label="Face-detection progress"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow={progress}
      >
        <div
          className="h-full rounded-full bg-brand-600 transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>
      <ol className="mt-6 grid gap-3 sm:grid-cols-2">
        {FACE_DETECTION_STAGES.map((stage, index) => (
          <li
            key={stage}
            className={`flex items-center gap-3 text-sm ${
              index <= activeIndex ? "font-semibold text-slate-900" : "text-slate-500"
            }`}
          >
            <span
              className={`h-2.5 w-2.5 shrink-0 rounded-full ${
                index < activeIndex
                  ? "bg-leaf-600"
                  : index === activeIndex
                    ? "animate-pulse bg-brand-600"
                    : "bg-slate-300"
              }`}
            />
            {stage}
          </li>
        ))}
      </ol>
    </div>
  );
}

function DetectionFact({ icon: Icon, label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
        <div>
          <dt className="text-sm font-semibold text-slate-600">{label}</dt>
          <dd className="mt-1 text-lg font-bold text-slate-950">{value}</dd>
        </div>
      </div>
    </div>
  );
}

export default function FaceDetectionPage() {
  const navigate = useNavigate();
  const startedRef = useRef(false);
  const [showWarningConfirmation, setShowWarningConfirmation] = useState(false);
  const [actionError, setActionError] = useState("");
  const {
    faceReport,
    isDetecting,
    isAcceptingWarning,
    detectionProgress,
    error,
    analyze,
    acceptWarning,
    clearFaceDetectionState,
  } = useFaceDetection();
  const { clearQualityState } = useImageQuality();
  const {
    isDeleting,
    serverError,
    deleteCurrentUpload,
    clearUploadReference,
  } = useUpload();

  useEffect(() => {
    if (!faceReport && !isDetecting && !error && !startedRef.current) {
      startedRef.current = true;
      analyze().catch(() => {});
    }
  }, [faceReport, isDetecting, error, analyze]);

  const handleAnalyzeAgain = async () => {
    if (isDetecting) return;
    setActionError("");
    setShowWarningConfirmation(false);
    try {
      await analyze();
    } catch {
      // A user-safe message is exposed through the context.
    }
  };

  const handleUploadAnother = async () => {
    if (isDeleting) return;
    setActionError("");
    try {
      await deleteCurrentUpload();
      clearFaceDetectionState();
      clearQualityState();
      clearUploadReference();
      navigate(ROUTES.faceScan, {
        replace: true,
        state: { uploadDeleted: true },
      });
    } catch {
      setActionError("Unable to remove the current image. Please try again.");
    }
  };

  const handleAcceptWarning = async () => {
    if (isAcceptingWarning) return;
    setActionError("");
    try {
      const response = await acceptWarning();
      navigate(response.next_route || ROUTES.imagePreprocessing);
    } catch {
      setActionError("Unable to record your warning acceptance. Please try again.");
    }
  };

  if (isDetecting && !faceReport) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader
          eyebrow="Face detection"
          title="Checking Face Suitability"
          description="Verifying that the image contains exactly one usable face before deterministic preprocessing."
        />
        <DetectionProgress progress={detectionProgress} />
        <div className="mx-auto mt-6 max-w-3xl">
          <DisclaimerBox title="Face detection is not diagnosis" />
        </div>
      </section>
    );
  }

  if (!faceReport) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader
          eyebrow="Face detection unavailable"
          title="We Could Not Complete Face Detection"
          description="No face recognition, skin analysis, diagnosis, or recommendation was performed."
        />
        <div className="mx-auto max-w-3xl border-y border-slate-200 py-8 text-center">
          <ErrorMessage id="face-detection-error" message={error} />
          <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
            <SecondaryButton
              type="button"
              icon={UploadCloud}
              onClick={handleUploadAnother}
              disabled={isDeleting}
            >
              Upload Another Image
            </SecondaryButton>
            <PrimaryButton type="button" icon={RefreshCcw} onClick={handleAnalyzeAgain}>
              Try Face Detection Again
            </PrimaryButton>
          </div>
        </div>
      </section>
    );
  }

  const statusDetail = STATUS_DETAILS[faceReport.detection_status];
  const StatusIcon = statusDetail.icon;

  return (
    <section className="px-4 py-14 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="Face detection report"
        title="Face Detection Results"
        description="Review whether the image contains one usable facial region. This step does not identify the person or analyze skin concerns."
      />

      <div className="mx-auto max-w-6xl space-y-10">
        {isDetecting ? (
          <div className="rounded-lg border border-brand-100 bg-brand-50 px-4 py-3 text-sm font-semibold text-brand-800" role="status">
            Rechecking the image with the backend detector: {detectionProgress}%
          </div>
        ) : null}

        <section className="grid gap-6 border-y border-slate-200 py-8 md:grid-cols-[12rem_1fr] md:items-center">
          <div className="text-center md:text-left">
            <p className="text-sm font-semibold text-slate-600">Faces Detected</p>
            <p className="mt-2 text-5xl font-bold text-slate-950">
              {faceReport.face_count}
            </p>
          </div>
          <div className={`rounded-lg border p-5 ${statusDetail.classes}`}>
            <div className="flex items-start gap-3">
              <StatusIcon className="mt-0.5 h-6 w-6 shrink-0" aria-hidden="true" />
              <div>
                <h2 className="text-lg font-semibold">{statusDetail.label}</h2>
                <p className="mt-1 text-sm leading-6">{statusDetail.description}</p>
              </div>
            </div>
          </div>
        </section>

        <section aria-labelledby="face-detection-summary-heading">
          <h2
            id="face-detection-summary-heading"
            className="text-2xl font-bold text-slate-950"
          >
            Detection checks
          </h2>
          <dl className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <DetectionFact
              icon={ScanFace}
              label="Detection confidence"
              value={
                faceReport.detection_confidence !== null
                  ? `${faceReport.detection_confidence}%`
                  : "Not available"
              }
            />
            <DetectionFact
              icon={Focus}
              label="Face position"
              value={statusText(faceReport.face_position)}
            />
            <DetectionFact
              icon={UserRoundCheck}
              label="Face size"
              value={statusText(faceReport.face_size)}
            />
            <DetectionFact
              icon={Crop}
              label="Facial region"
              value={
                faceReport.crop.prepared
                  ? `${faceReport.crop.width} x ${faceReport.crop.height}`
                  : "Not prepared"
              }
            />
          </dl>
        </section>

        <section aria-labelledby="face-issues-heading">
          <h2 id="face-issues-heading" className="text-2xl font-bold text-slate-950">
            {faceReport.issues.length ? "Issues and improvements" : "No face-detection issues found"}
          </h2>
          {faceReport.issues.length ? (
            <div className="mt-5 grid gap-4">
              {faceReport.issues.map((issue) => (
                <article
                  key={issue.code}
                  className={`rounded-lg border p-5 ${
                    issue.severity === "error"
                      ? "border-red-200 bg-red-50"
                      : "border-amber-200 bg-amber-50"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {issue.severity === "error" ? (
                      <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-700" aria-hidden="true" />
                    ) : (
                      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" aria-hidden="true" />
                    )}
                    <div>
                      <h3 className="font-semibold text-slate-950">{issue.message}</h3>
                      <p className="mt-2 text-sm leading-6 text-slate-700">
                        {issue.recommendation}
                      </p>
                      <p className="mt-2 text-xs font-semibold text-slate-500">
                        Reference: {issue.code}
                      </p>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="mt-5 flex items-start gap-3 border-y border-leaf-200 bg-leaf-50 px-4 py-5">
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-leaf-700" aria-hidden="true" />
              <p className="text-sm leading-6 text-slate-700">
                The configured face-count, confidence, position, size, boundary, and
                crop checks did not identify a technical concern.
              </p>
            </div>
          )}
        </section>

        <details className="border-y border-slate-200 py-5">
          <summary className="cursor-pointer text-sm font-semibold text-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600">
            View technical details
          </summary>
          <dl className="mt-5 grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
            <div><dt className="font-semibold text-slate-950">Faces detected</dt><dd className="mt-1 text-slate-600">{faceReport.face_count}</dd></div>
            <div><dt className="font-semibold text-slate-950">Position status</dt><dd className="mt-1 text-slate-600">{statusText(faceReport.face_position)}</dd></div>
            <div><dt className="font-semibold text-slate-950">Size status</dt><dd className="mt-1 text-slate-600">{statusText(faceReport.face_size)}</dd></div>
            <div><dt className="font-semibold text-slate-950">Report status</dt><dd className="mt-1 capitalize text-slate-600">{faceReport.detection_status}</dd></div>
          </dl>
        </details>

        {showWarningConfirmation && faceReport.detection_status === "warning" ? (
          <section className="rounded-lg border border-amber-300 bg-amber-50 p-5" aria-labelledby="face-warning-confirmation-heading">
            <div className="flex items-start gap-3">
              <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-amber-800" aria-hidden="true" />
              <div>
                <h2 id="face-warning-confirmation-heading" className="font-semibold text-slate-950">
                  Continue with this face-detection warning?
                </h2>
                <p className="mt-2 text-sm leading-6 text-slate-700">
                  Continuing may reduce the reliability of the prepared model input.
                  This confirmation records only your acceptance of the technical
                  warning.
                </p>
                <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                  <SecondaryButton type="button" onClick={() => setShowWarningConfirmation(false)}>
                    Cancel
                  </SecondaryButton>
                  <PrimaryButton
                    type="button"
                    icon={ArrowRight}
                    onClick={handleAcceptWarning}
                    disabled={isAcceptingWarning}
                  >
                    {isAcceptingWarning ? "Recording Acceptance..." : "Confirm and Continue"}
                  </PrimaryButton>
                </div>
              </div>
            </div>
          </section>
        ) : null}

        <div className="rounded-lg border border-clinic-100 bg-clinic-50 p-5">
          <div className="flex items-start gap-3">
            <Eye className="mt-0.5 h-5 w-5 shrink-0 text-clinic-700" aria-hidden="true" />
            <p className="text-sm leading-6 text-slate-700">
              DermaScan AI checks whether one usable face is present. It does not
              identify the person and does not perform facial recognition.
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <p className="text-sm leading-6 text-slate-700">
            Face detection is used only to prepare the facial region for general
            skincare analysis. It is not used for identity verification or medical
            diagnosis.
          </p>
        </div>

        <DisclaimerBox title="Face detection is not diagnosis" />
        <ErrorMessage
          id="face-detection-action-error"
          message={actionError || error || serverError}
        />

        <div className="flex flex-col-reverse gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:justify-between">
          <SecondaryButton
            type="button"
            icon={UploadCloud}
            onClick={handleUploadAnother}
            disabled={isDeleting || isAcceptingWarning || isDetecting}
          >
            {isDeleting ? "Removing Image..." : "Upload a Better Image"}
          </SecondaryButton>

          <div className="flex flex-col gap-3 sm:flex-row">
            {faceReport.detection_status !== "failed" ? (
              <SecondaryButton
                type="button"
                icon={RefreshCcw}
                onClick={handleAnalyzeAgain}
                disabled={isDetecting || isAcceptingWarning}
              >
                Recheck Face Detection
              </SecondaryButton>
            ) : null}

            {faceReport.detection_status === "passed" ? (
              <PrimaryButton
                type="button"
                icon={ArrowRight}
                onClick={() => navigate(faceReport.next_route || ROUTES.imagePreprocessing)}
              >
                Continue to Image Preprocessing
              </PrimaryButton>
            ) : null}

            {faceReport.detection_status === "warning" && !faceReport.can_continue ? (
              <PrimaryButton
                type="button"
                icon={ArrowRight}
                onClick={() => setShowWarningConfirmation(true)}
                disabled={showWarningConfirmation || isAcceptingWarning}
              >
                Continue with Current Image
              </PrimaryButton>
            ) : null}

            {faceReport.detection_status === "warning" && faceReport.can_continue ? (
              <PrimaryButton
                type="button"
                icon={ArrowRight}
                onClick={() => navigate(faceReport.next_route || ROUTES.imagePreprocessing)}
              >
                Continue to Image Preprocessing
              </PrimaryButton>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}
