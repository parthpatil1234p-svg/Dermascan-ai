import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Droplets,
  Maximize2,
  Palette,
  RefreshCcw,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  XCircle,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import DisclaimerBox from "../components/DisclaimerBox";
import ErrorMessage from "../components/ErrorMessage";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import { IMAGE_PREPROCESSING_STAGES, ROUTES } from "../constants/appContent";
import { useFaceDetection } from "../context/FaceDetectionContext";
import { useImagePreprocessing } from "../context/ImagePreprocessingContext";
import { useImageQuality } from "../context/ImageQualityContext";
import { useUpload } from "../context/UploadContext";

const STATUS_DETAILS = {
  completed: {
    label: "Image Preparation Completed",
    description: "The facial crop now matches the configured model-input contract.",
    icon: CheckCircle2,
    classes: "border-leaf-200 bg-leaf-50 text-leaf-800",
  },
  warning: {
    label: "Prepared with a Technical Warning",
    description: "The model input is valid, but a better source image is recommended.",
    icon: AlertTriangle,
    classes: "border-amber-200 bg-amber-50 text-amber-900",
  },
  failed: {
    label: "Image Preparation Failed",
    description: "This image cannot continue to future model inference.",
    icon: XCircle,
    classes: "border-red-200 bg-red-50 text-red-800",
  },
  expired: {
    label: "Prepared Image Expired",
    description: "The temporary derivative is no longer available.",
    icon: XCircle,
    classes: "border-red-200 bg-red-50 text-red-800",
  },
};

function ProcessingProgress({ progress }) {
  const activeIndex = Math.min(
    IMAGE_PREPROCESSING_STAGES.length - 1,
    Math.floor((progress / 100) * IMAGE_PREPROCESSING_STAGES.length),
  );

  return (
    <div className="mx-auto max-w-3xl border-y border-slate-200 py-8" role="status">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-950">
            Preparing a consistent model input
          </h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            The backend is standardizing technical image properties without applying
            beauty filters or skin analysis.
          </p>
        </div>
        <span className="text-lg font-bold text-brand-700">{progress}%</span>
      </div>
      <div
        className="mt-5 h-2 overflow-hidden rounded-full bg-slate-200"
        role="progressbar"
        aria-label="Image-preprocessing progress"
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
        {IMAGE_PREPROCESSING_STAGES.map((stage, index) => (
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

function PreparationFact({ icon: Icon, label, value }) {
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

export default function ImagePreprocessingPage() {
  const navigate = useNavigate();
  const startedRef = useRef(false);
  const [actionError, setActionError] = useState("");
  const {
    preprocessingReport,
    isProcessing,
    processingProgress,
    error,
    processCurrentImage,
    reprocessCurrentImage,
    clearPreprocessingState,
  } = useImagePreprocessing();
  const { clearFaceDetectionState } = useFaceDetection();
  const { clearQualityState } = useImageQuality();
  const {
    isDeleting,
    serverError,
    deleteCurrentUpload,
    clearUploadReference,
  } = useUpload();

  useEffect(() => {
    if (!preprocessingReport && !isProcessing && !error && !startedRef.current) {
      startedRef.current = true;
      processCurrentImage().catch(() => {});
    }
  }, [preprocessingReport, isProcessing, error, processCurrentImage]);

  const handleRetry = async () => {
    if (isProcessing) return;
    setActionError("");
    try {
      await reprocessCurrentImage();
    } catch {
      // The context exposes a safe user-facing message.
    }
  };

  const handleUploadAnother = async () => {
    if (isDeleting) return;
    setActionError("");
    try {
      await deleteCurrentUpload();
      clearPreprocessingState();
      clearFaceDetectionState();
      clearQualityState();
      clearUploadReference();
      navigate(ROUTES.faceScan, { replace: true, state: { uploadDeleted: true } });
    } catch {
      setActionError("Unable to remove the current image. Please try again.");
    }
  };

  if (isProcessing && !preprocessingReport) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader
          eyebrow="Image preprocessing"
          title="Preparing Facial Image"
          description="Standardizing colour channels, dimensions, and pixel values for a future model input."
        />
        <ProcessingProgress progress={processingProgress} />
        <div className="mx-auto mt-6 max-w-3xl">
          <DisclaimerBox title="Technical preparation only" />
        </div>
      </section>
    );
  }

  if (!preprocessingReport) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader
          eyebrow="Image preparation unavailable"
          title="We Could Not Prepare This Image"
          description="No skin type, skin concern, identity, or medical analysis was performed."
        />
        <div className="mx-auto max-w-3xl border-y border-slate-200 py-8 text-center">
          <ErrorMessage id="preprocessing-error" message={error} />
          <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
            <SecondaryButton type="button" icon={UploadCloud} onClick={handleUploadAnother} disabled={isDeleting}>
              Upload Another Image
            </SecondaryButton>
            <PrimaryButton type="button" icon={RefreshCcw} onClick={handleRetry} disabled={isProcessing}>
              Try Again
            </PrimaryButton>
          </div>
        </div>
      </section>
    );
  }

  const statusDetail = STATUS_DETAILS[preprocessingReport.preprocessing_status];
  const StatusIcon = statusDetail.icon;
  const modelInput = preprocessingReport.model_input;
  const transformations = preprocessingReport.transformations;

  return (
    <section className="px-4 py-14 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="Image preparation report"
        title="Facial Image Prepared"
        description="Review how the private facial crop was standardized for future machine-learning inference."
      />

      <div className="mx-auto max-w-6xl space-y-10">
        {isProcessing ? (
          <div className="rounded-lg border border-brand-100 bg-brand-50 px-4 py-3 text-sm font-semibold text-brand-800" role="status">
            Reprocessing the private facial crop: {processingProgress}%
          </div>
        ) : null}

        <section className="grid gap-6 border-y border-slate-200 py-8 md:grid-cols-[13rem_1fr] md:items-center">
          <div className="text-center md:text-left">
            <p className="text-sm font-semibold text-slate-600">Model Input</p>
            <p className="mt-2 text-3xl font-bold text-slate-950">
              {modelInput.width} x {modelInput.height}
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

        <section aria-labelledby="preparation-summary-heading">
          <h2 id="preparation-summary-heading" className="text-2xl font-bold text-slate-950">
            Preparation summary
          </h2>
          <dl className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <PreparationFact icon={Palette} label="Colour format" value={modelInput.colour_space} />
            <PreparationFact icon={Maximize2} label="Aspect ratio" value="Preserved" />
            <PreparationFact icon={Droplets} label="Normalization" value="0 to 1 at inference" />
            <PreparationFact icon={Sparkles} label="Beauty filters" value="None" />
          </dl>
        </section>

        {preprocessingReport.issues.length ? (
          <section aria-labelledby="preprocessing-issues-heading">
            <h2 id="preprocessing-issues-heading" className="text-2xl font-bold text-slate-950">
              Technical warnings
            </h2>
            <div className="mt-5 grid gap-4">
              {preprocessingReport.issues.map((issue) => (
                <article key={issue.code} className="rounded-lg border border-amber-200 bg-amber-50 p-5">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" aria-hidden="true" />
                    <div>
                      <h3 className="font-semibold text-slate-950">{issue.message}</h3>
                      <p className="mt-2 text-sm leading-6 text-slate-700">{issue.recommendation}</p>
                      <p className="mt-2 text-xs font-semibold text-slate-500">Reference: {issue.code}</p>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>
        ) : (
          <div className="flex items-start gap-3 border-y border-leaf-200 bg-leaf-50 px-4 py-5">
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-leaf-700" aria-hidden="true" />
            <p className="text-sm leading-6 text-slate-700">
              The output passed size, channel, pixel-range, decode, and variation checks.
            </p>
          </div>
        )}

        <details className="border-y border-slate-200 py-5">
          <summary className="cursor-pointer text-sm font-semibold text-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600">
            View technical details
          </summary>
          <dl className="mt-5 grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
            <div><dt className="font-semibold text-slate-950">Channels</dt><dd className="mt-1 text-slate-600">{modelInput.channels}</dd></div>
            <div><dt className="font-semibold text-slate-950">Resize mode</dt><dd className="mt-1 capitalize text-slate-600">{transformations.resize_mode}</dd></div>
            <div><dt className="font-semibold text-slate-950">Padding</dt><dd className="mt-1 text-slate-600">{transformations.padding_applied ? "Applied" : "Not required"}</dd></div>
            <div><dt className="font-semibold text-slate-950">Denoising</dt><dd className="mt-1 text-slate-600">{transformations.denoise_applied ? "Mild" : "Skipped"}</dd></div>
            <div><dt className="font-semibold text-slate-950">Illumination adjustment</dt><dd className="mt-1 text-slate-600">{transformations.illumination_adjustment_applied ? "Applied" : "Disabled"}</dd></div>
            <div><dt className="font-semibold text-slate-950">White balance</dt><dd className="mt-1 text-slate-600">{transformations.white_balance_applied ? "Applied" : "Disabled"}</dd></div>
            <div><dt className="font-semibold text-slate-950">Sharpening</dt><dd className="mt-1 text-slate-600">{transformations.sharpening_applied ? "Applied" : "Disabled"}</dd></div>
            <div><dt className="font-semibold text-slate-950">Inference tensor</dt><dd className="mt-1 text-slate-600">float32, batch dimension added later</dd></div>
          </dl>
        </details>

        <div className="rounded-lg border border-clinic-100 bg-clinic-50 p-5">
          <div className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-clinic-700" aria-hidden="true" />
            <p className="text-sm leading-6 text-slate-700">
              Image preprocessing standardizes technical image properties. It does not identify the user, diagnose a skin condition, improve physical appearance, or predict skin type.
            </p>
          </div>
        </div>

        <DisclaimerBox title="Technical preparation is not diagnosis" />
        <ErrorMessage id="preprocessing-action-error" message={actionError || error || serverError} />

        <div className="flex flex-col-reverse gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:justify-between">
          <SecondaryButton type="button" icon={UploadCloud} onClick={handleUploadAnother} disabled={isDeleting || isProcessing}>
            {isDeleting ? "Removing Image..." : "Upload a Better Image"}
          </SecondaryButton>
          <div className="flex flex-col gap-3 sm:flex-row">
            <SecondaryButton type="button" icon={RefreshCcw} onClick={handleRetry} disabled={isProcessing || isDeleting}>
              Reprocess Image
            </SecondaryButton>
            {preprocessingReport.can_continue ? (
              <PrimaryButton type="button" icon={ArrowRight} onClick={() => navigate(preprocessingReport.next_route || ROUTES.skinTypeAnalysis)}>
                {preprocessingReport.preprocessing_status === "warning"
                  ? "Continue with Prepared Image"
                  : "Continue to Skin Type Analysis"}
              </PrimaryButton>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}
