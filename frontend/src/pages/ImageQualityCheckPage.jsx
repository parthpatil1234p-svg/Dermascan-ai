import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Contrast,
  Focus,
  Gauge,
  Lightbulb,
  Maximize2,
  RefreshCcw,
  ShieldCheck,
  Sun,
  UploadCloud,
  XCircle,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import DisclaimerBox from "../components/DisclaimerBox";
import ErrorMessage from "../components/ErrorMessage";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import QualityMetricCard from "../components/QualityMetricCard";
import SecondaryButton from "../components/SecondaryButton";
import { IMAGE_QUALITY_STAGES, ROUTES } from "../constants/appContent";
import { useImageQuality } from "../context/ImageQualityContext";
import { useUpload } from "../context/UploadContext";

const STATUS_DETAILS = {
  passed: {
    label: "Suitable for Face Detection",
    description: "Your image meets the current technical quality requirements.",
    icon: CheckCircle2,
    classes: "border-leaf-200 bg-leaf-50 text-leaf-800",
  },
  warning: {
    label: "Usable with Caution",
    description: "The image may continue, but a clearer replacement is recommended.",
    icon: AlertTriangle,
    classes: "border-amber-200 bg-amber-50 text-amber-900",
  },
  failed: {
    label: "New Image Required",
    description: "This image cannot continue to reliable face analysis.",
    icon: XCircle,
    classes: "border-red-200 bg-red-50 text-red-800",
  },
};

function AnalysisProgress({ progress }) {
  const activeIndex = Math.min(
    IMAGE_QUALITY_STAGES.length - 1,
    Math.floor((progress / 100) * IMAGE_QUALITY_STAGES.length),
  );

  return (
    <div className="mx-auto max-w-3xl border-y border-slate-200 py-8" role="status">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-950">
            Checking technical image quality
          </h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            The result shown here will come from the backend quality service.
          </p>
        </div>
        <span className="text-lg font-bold text-brand-700">{progress}%</span>
      </div>
      <div
        className="mt-5 h-2 overflow-hidden rounded-full bg-slate-200"
        role="progressbar"
        aria-label="Image-quality analysis progress"
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
        {IMAGE_QUALITY_STAGES.map((stage, index) => (
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

export default function ImageQualityCheckPage() {
  const navigate = useNavigate();
  const startedRef = useRef(false);
  const [showWarningConfirmation, setShowWarningConfirmation] = useState(false);
  const [actionError, setActionError] = useState("");
  const {
    qualityReport,
    isAnalyzing,
    isAcceptingWarning,
    analysisProgress,
    error,
    analyze,
    acceptWarning,
    clearQualityState,
  } = useImageQuality();
  const {
    isDeleting,
    serverError,
    deleteCurrentUpload,
    clearUploadReference,
  } = useUpload();

  useEffect(() => {
    if (!qualityReport && !isAnalyzing && !error && !startedRef.current) {
      startedRef.current = true;
      analyze().catch(() => {});
    }
  }, [qualityReport, isAnalyzing, error, analyze]);

  const handleAnalyzeAgain = async () => {
    if (isAnalyzing) return;
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
      navigate(response.next_route || ROUTES.faceDetection);
    } catch {
      setActionError("Unable to record your warning acceptance. Please try again.");
    }
  };

  if (isAnalyzing && !qualityReport) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader
          eyebrow="Technical image check"
          title="Evaluating Image Quality"
          description="Checking whether the sanitized image has enough technical quality for the next development module."
        />
        <AnalysisProgress progress={analysisProgress} />
        <div className="mx-auto mt-6 max-w-3xl">
          <DisclaimerBox title="Technical heuristics only" />
        </div>
      </section>
    );
  }

  if (!qualityReport) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader
          eyebrow="Quality check unavailable"
          title="We Could Not Complete the Check"
          description="Your image has not been diagnosed or analyzed for skin concerns."
        />
        <div className="mx-auto max-w-3xl border-y border-slate-200 py-8 text-center">
          <ErrorMessage id="image-quality-error" message={error} />
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
              Try Quality Check Again
            </PrimaryButton>
          </div>
        </div>
      </section>
    );
  }

  const statusDetail = STATUS_DETAILS[qualityReport.quality_status];
  const StatusIcon = statusDetail.icon;
  const { metrics } = qualityReport;

  return (
    <section className="px-4 py-14 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="Technical quality report"
        title="Image Quality Results"
        description="Review the image-level technical checks before continuing. These measurements are not skin analysis or diagnosis."
      />

      <div className="mx-auto max-w-6xl space-y-10">
        {isAnalyzing ? (
          <div className="rounded-lg border border-brand-100 bg-brand-50 px-4 py-3 text-sm font-semibold text-brand-800" role="status">
            Rechecking the image with the backend quality service: {analysisProgress}%
          </div>
        ) : null}
        <section className="grid gap-6 border-y border-slate-200 py-8 md:grid-cols-[12rem_1fr] md:items-center">
          <div className="text-center md:text-left">
            <p className="text-sm font-semibold text-slate-600">Image Quality Score</p>
            <p className="mt-2 text-5xl font-bold text-slate-950">
              {qualityReport.quality_score}
              <span className="text-xl text-slate-500">/100</span>
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

        <section aria-labelledby="metric-heading">
          <h2 id="metric-heading" className="text-2xl font-bold text-slate-950">
            Quality checks
          </h2>
          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <QualityMetricCard
              icon={Focus}
              label="Sharpness"
              status={metrics.sharpness.status}
              score={metrics.sharpness.score}
              detail="Estimates blur from visible edge detail across the complete image."
            />
            <QualityMetricCard
              icon={Sun}
              label="Brightness"
              status={metrics.brightness.status}
              score={metrics.brightness.score}
              detail={`Average luminance: ${metrics.brightness.mean} on a 0-255 scale.`}
            />
            <QualityMetricCard
              icon={Gauge}
              label="Exposure"
              status={metrics.exposure.status}
              score={metrics.exposure.score}
              detail={`${metrics.exposure.underexposed_percent}% dark and ${metrics.exposure.overexposed_percent}% bright pixels.`}
            />
            <QualityMetricCard
              icon={Contrast}
              label="Contrast"
              status={metrics.contrast.status}
              score={metrics.contrast.score}
              detail="Checks whether the complete image retains a useful range of visible detail."
            />
            <QualityMetricCard
              icon={Maximize2}
              label="Resolution"
              status={metrics.resolution.status}
              score={metrics.resolution.score}
              detail={`${metrics.resolution.width} x ${metrics.resolution.height} pixels.`}
            />
          </div>
        </section>

        <section aria-labelledby="issue-heading">
          <h2 id="issue-heading" className="text-2xl font-bold text-slate-950">
            {qualityReport.issues.length ? "Issues and improvements" : "No quality issues found"}
          </h2>
          {qualityReport.issues.length ? (
            <div className="mt-5 grid gap-4">
              {qualityReport.issues.map((issue) => (
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
                The configured image-level sharpness, lighting, contrast, resolution,
                and aspect-ratio checks did not identify a technical concern.
              </p>
            </div>
          )}
        </section>

        <details className="border-y border-slate-200 py-5">
          <summary className="cursor-pointer text-sm font-semibold text-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600">
            View technical details
          </summary>
          <dl className="mt-5 grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
            <div><dt className="font-semibold text-slate-950">Mean brightness</dt><dd className="mt-1 text-slate-600">{metrics.brightness.mean}</dd></div>
            <div><dt className="font-semibold text-slate-950">Contrast value</dt><dd className="mt-1 text-slate-600">{metrics.contrast.value}</dd></div>
            <div><dt className="font-semibold text-slate-950">Aspect ratio</dt><dd className="mt-1 text-slate-600">{metrics.resolution.aspect_ratio}</dd></div>
            <div><dt className="font-semibold text-slate-950">Report status</dt><dd className="mt-1 capitalize text-slate-600">{qualityReport.quality_status}</dd></div>
          </dl>
        </details>

        {showWarningConfirmation && qualityReport.quality_status === "warning" ? (
          <section className="rounded-lg border border-amber-300 bg-amber-50 p-5" aria-labelledby="warning-confirmation-heading">
            <div className="flex items-start gap-3">
              <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-amber-800" aria-hidden="true" />
              <div>
                <h2 id="warning-confirmation-heading" className="font-semibold text-slate-950">
                  Continue with this quality warning?
                </h2>
                <p className="mt-2 text-sm leading-6 text-slate-700">
                  Continuing may reduce the reliability of future face checks. This
                  confirmation records only your acceptance of the technical warning.
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
            <Lightbulb className="mt-0.5 h-5 w-5 shrink-0 text-clinic-700" aria-hidden="true" />
            <p className="text-sm leading-6 text-slate-700">
              These thresholds are configurable MVP heuristics applied to the complete
              image. Face-region lighting checks will be more precise only after face
              detection is implemented.
            </p>
          </div>
        </div>

        <DisclaimerBox title="Quality measurements are not diagnosis" />
        <ErrorMessage
          id="image-quality-action-error"
          message={actionError || error || serverError}
        />

        <div className="flex flex-col-reverse gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:justify-between">
          <SecondaryButton
            type="button"
            icon={UploadCloud}
            onClick={handleUploadAnother}
            disabled={isDeleting || isAcceptingWarning || isAnalyzing}
          >
            {isDeleting ? "Removing Image..." : "Upload a Better Image"}
          </SecondaryButton>

          <div className="flex flex-col gap-3 sm:flex-row">
            {qualityReport.quality_status !== "failed" ? (
              <SecondaryButton
                type="button"
                icon={RefreshCcw}
                onClick={handleAnalyzeAgain}
                disabled={isAnalyzing || isAcceptingWarning}
              >
                Recheck Image
              </SecondaryButton>
            ) : null}

            {qualityReport.quality_status === "passed" ? (
              <PrimaryButton
                type="button"
                icon={ArrowRight}
                onClick={() => navigate(qualityReport.next_route || ROUTES.faceDetection)}
              >
                Continue to Face Detection
              </PrimaryButton>
            ) : null}

            {qualityReport.quality_status === "warning" && !qualityReport.can_continue ? (
              <PrimaryButton
                type="button"
                icon={ArrowRight}
                onClick={() => setShowWarningConfirmation(true)}
                disabled={showWarningConfirmation || isAcceptingWarning}
              >
                Continue with Current Image
              </PrimaryButton>
            ) : null}

            {qualityReport.quality_status === "warning" && qualityReport.can_continue ? (
              <PrimaryButton
                type="button"
                icon={ArrowRight}
                onClick={() => navigate(qualityReport.next_route || ROUTES.faceDetection)}
              >
                Continue to Face Detection
              </PrimaryButton>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}
