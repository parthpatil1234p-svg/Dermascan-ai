import {
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  Info,
  MapPin,
  RefreshCcw,
  ShieldCheck,
  UploadCloud,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import DisclaimerBox from "../components/DisclaimerBox";
import DemoModeNotice from "../components/DemoModeNotice";
import ErrorMessage from "../components/ErrorMessage";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import { ROUTES, SKIN_CONCERN_ANALYSIS_STAGES } from "../constants/appContent";
import { useFaceDetection } from "../context/FaceDetectionContext";
import { useImagePreprocessing } from "../context/ImagePreprocessingContext";
import { useImageQuality } from "../context/ImageQualityContext";
import { useSkinConcern } from "../context/SkinConcernContext";
import { useSkinType } from "../context/SkinTypeContext";
import { useUpload } from "../context/UploadContext";

const ISSUE_MESSAGES = {
  REGION_INFORMATION_UNAVAILABLE:
    "Precise facial regions are not available in this model stage. Observed labels are reported for the full prepared face only.",
};

function AnalysisProgress({ progress }) {
  const activeIndex = Math.min(
    SKIN_CONCERN_ANALYSIS_STAGES.length - 1,
    Math.floor((progress / 100) * SKIN_CONCERN_ANALYSIS_STAGES.length),
  );
  return (
    <div className="mx-auto max-w-3xl border-y border-slate-200 py-8" role="status">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-950">Reviewing visible characteristics</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            The validated multi-label model is checking independent visible labels and preserving uncertainty.
          </p>
        </div>
        <span className="text-lg font-bold text-brand-700">{progress}%</span>
      </div>
      <div
        className="mt-5 h-2 overflow-hidden rounded-full bg-slate-200"
        role="progressbar"
        aria-label="Visible skin-concern analysis progress"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow={progress}
      >
        <div className="h-full rounded-full bg-brand-600 transition-all" style={{ width: `${progress}%` }} />
      </div>
      <ol className="mt-6 grid gap-3 sm:grid-cols-2">
        {SKIN_CONCERN_ANALYSIS_STAGES.map((stage, index) => (
          <li
            key={stage}
            className={`flex items-center gap-3 text-sm ${index <= activeIndex ? "font-semibold text-slate-900" : "text-slate-500"}`}
          >
            <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${index < activeIndex ? "bg-leaf-600" : index === activeIndex ? "animate-pulse bg-brand-600" : "bg-slate-300"}`} />
            {stage}
          </li>
        ))}
      </ol>
    </div>
  );
}

function ObservationCard({ observation, uncertain = false }) {
  return (
    <article className={`rounded-lg border bg-white p-5 shadow-sm ${uncertain ? "border-amber-200" : "border-slate-200"}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Visible observation</p>
          <h3 className="mt-1 text-lg font-semibold text-slate-950">{observation.name}</h3>
        </div>
        <span className={`rounded-md px-2.5 py-1 text-xs font-bold ${uncertain ? "bg-amber-100 text-amber-900" : "bg-leaf-100 text-leaf-900"}`}>
          {uncertain ? "Uncertain" : observation.visible_severity}
        </span>
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-3 border-y border-slate-100 py-3 text-sm">
        <div>
          <dt className="text-slate-500">Model confidence</dt>
          <dd className="mt-1 font-semibold text-slate-900">{observation.confidence}%</dd>
        </div>
        <div>
          <dt className="text-slate-500">Status</dt>
          <dd className="mt-1 font-semibold capitalize text-slate-900">{observation.status}</dd>
        </div>
      </dl>
      <p className="mt-4 text-sm leading-6 text-slate-700">{observation.explanation}</p>
      {observation.regions.length ? (
        <p className="mt-3 flex items-center gap-2 text-sm text-slate-600">
          <MapPin className="h-4 w-4 shrink-0 text-brand-700" aria-hidden="true" />
          Scope: {observation.regions.join(", ")}
        </p>
      ) : null}
      {observation.questionnaire_agreement !== "Not Compared" ? (
        <div className="mt-4 rounded-md bg-clinic-50 p-3 text-sm leading-6 text-slate-700">
          <p>
            <strong>Self-reported value:</strong>{" "}
            {observation.questionnaire_reported_value || "Not specified"}
          </p>
          <p className="mt-1">
            <strong>{observation.questionnaire_agreement} questionnaire comparison:</strong>{" "}
            {observation.questionnaire_explanation}
          </p>
        </div>
      ) : null}
      <p className="mt-4 text-xs leading-5 text-slate-500">{observation.limitations.join(" ")}</p>
    </article>
  );
}

export default function SkinConcernAnalysisPage() {
  const navigate = useNavigate();
  const startedRef = useRef(false);
  const [actionError, setActionError] = useState("");
  const {
    concernReport,
    modelStatus,
    isCheckingModel,
    isAnalyzing,
    analysisProgress,
    error,
    checkModelReadiness,
    analyzeCurrentImage,
    clearConcernState,
  } = useSkinConcern();
  const { clearSkinTypeState } = useSkinType();
  const { clearPreprocessingState } = useImagePreprocessing();
  const { clearFaceDetectionState } = useFaceDetection();
  const { clearQualityState } = useImageQuality();
  const { isDeleting, deleteCurrentUpload, clearUploadReference } = useUpload();

  useEffect(() => {
    if (concernReport || isCheckingModel || isAnalyzing || error || startedRef.current) return;
    startedRef.current = true;
    const start = async () => {
      const status = await checkModelReadiness();
      if (status.loaded) await analyzeCurrentImage();
    };
    start().catch(() => {});
  }, [concernReport, isCheckingModel, isAnalyzing, error, checkModelReadiness, analyzeCurrentImage]);

  const handleRetry = async () => {
    if (isCheckingModel || isAnalyzing) return;
    setActionError("");
    try {
      const status = await checkModelReadiness();
      if (status.loaded) await analyzeCurrentImage();
    } catch {
      // The context exposes a safe user-facing message.
    }
  };

  const handleUploadAnother = async () => {
    if (isDeleting) return;
    setActionError("");
    try {
      await deleteCurrentUpload();
      clearConcernState();
      clearSkinTypeState();
      clearPreprocessingState();
      clearFaceDetectionState();
      clearQualityState();
      clearUploadReference();
      navigate(ROUTES.faceScan, { replace: true, state: { uploadDeleted: true } });
    } catch {
      setActionError("Unable to remove the current image. Please try again.");
    }
  };

  if ((isCheckingModel || isAnalyzing) && !concernReport) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader
          eyebrow="Visible characteristic review"
          title={isCheckingModel ? "Checking Model Readiness" : "Reviewing the Prepared Image"}
          description="This stage estimates independent visible labels. It does not identify diseases, causes, or treatments."
        />
        {isCheckingModel ? (
          <div className="mx-auto max-w-3xl border-y border-slate-200 py-10 text-center" role="status">
            <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
            <p className="mt-4 text-sm font-semibold text-slate-700">Verifying model, labels, metadata, and calibrated thresholds...</p>
          </div>
        ) : <AnalysisProgress progress={analysisProgress} />}
      </section>
    );
  }

  if (modelStatus && !modelStatus.loaded) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader
          eyebrow="Model unavailable"
          title="Visible Skin-Concern Analysis Is Not Ready"
          description="A validated compatible model and calibrated thresholds have not been installed. No observations were generated."
        />
        <div className="mx-auto max-w-3xl space-y-6">
          <div className="flex items-start gap-4 border-y border-amber-200 bg-amber-50 px-4 py-7">
            <AlertTriangle className="mt-0.5 h-6 w-6 shrink-0 text-amber-700" aria-hidden="true" />
            <div>
              <h2 className="font-semibold text-slate-950">Validated artifacts required</h2>
              <p className="mt-2 text-sm leading-6 text-slate-700">DermaScan AI will not substitute demo labels, default thresholds, or fabricated confidence scores.</p>
            </div>
          </div>
          <ErrorMessage id="concern-model-error" message={actionError || error} />
          <div className="flex flex-col gap-3 sm:flex-row sm:justify-between">
            <SecondaryButton type="button" icon={UploadCloud} onClick={handleUploadAnother} disabled={isDeleting}>Upload Another Image</SecondaryButton>
            <PrimaryButton type="button" icon={RefreshCcw} onClick={handleRetry} disabled={isCheckingModel}>Check Again</PrimaryButton>
          </div>
        </div>
      </section>
    );
  }

  if (!concernReport) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader eyebrow="Analysis unavailable" title="We Could Not Review Visible Characteristics" description="No diagnosis or product recommendation was performed." />
        <div className="mx-auto max-w-3xl border-y border-slate-200 py-8 text-center">
          <ErrorMessage id="concern-analysis-error" message={error || actionError} />
          <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
            <SecondaryButton type="button" icon={UploadCloud} onClick={handleUploadAnother} disabled={isDeleting}>Upload Another Image</SecondaryButton>
            <PrimaryButton type="button" icon={RefreshCcw} onClick={handleRetry} disabled={isAnalyzing}>Try Again</PrimaryButton>
          </div>
        </div>
      </section>
    );
  }

  const hasUncertainty = concernReport.overall_status === "completed_with_uncertainty";
  return (
    <section className="px-4 py-14 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="General visible observations"
        title="Visible Skin Characteristics"
        description="Independent labels are shown only when supported by the model threshold. Borderline scores remain visibly uncertain."
      />
      <div className="mx-auto max-w-6xl space-y-10">
        <DemoModeNotice visible={concernReport.analysis_mode === "demonstration"} />
        <section className={`flex items-start gap-4 border-y px-2 py-7 ${hasUncertainty ? "border-amber-200" : "border-leaf-200"}`}>
          {hasUncertainty ? <AlertTriangle className="mt-0.5 h-6 w-6 shrink-0 text-amber-700" aria-hidden="true" /> : <CheckCircle2 className="mt-0.5 h-6 w-6 shrink-0 text-leaf-700" aria-hidden="true" />}
          <div>
            <h2 className="text-xl font-semibold text-slate-950">{hasUncertainty ? "Review includes uncertain observations" : "Technical analysis completed"}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-700">Multiple characteristics may appear together. Absence from this report does not prove a characteristic is absent.</p>
          </div>
        </section>

        <section aria-labelledby="observed-heading">
          <h2 id="observed-heading" className="text-2xl font-bold text-slate-950">Observed or possible characteristics</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">Severity describes visible prominence in this image, not clinical severity.</p>
          {concernReport.observations.length ? (
            <div className="mt-6 grid gap-5 md:grid-cols-2">{concernReport.observations.map((item) => <ObservationCard key={item.code} observation={item} />)}</div>
          ) : (
            <div className="mt-6 flex items-start gap-3 border-y border-slate-200 py-6 text-sm text-slate-700"><Info className="h-5 w-5 shrink-0 text-brand-700" aria-hidden="true" />No visible label clearly exceeded its calibrated threshold.</div>
          )}
        </section>

        {concernReport.uncertain_observations.length ? (
          <section aria-labelledby="uncertain-heading">
            <h2 id="uncertain-heading" className="text-2xl font-bold text-slate-950">Uncertain observations</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">These scores were close to their label-specific threshold, so no definite visual claim is made.</p>
            <div className="mt-6 grid gap-5 md:grid-cols-2">{concernReport.uncertain_observations.map((item) => <ObservationCard key={item.code} observation={item} uncertain />)}</div>
          </section>
        ) : null}

        {concernReport.issues.length ? (
          <aside className="flex items-start gap-3 rounded-lg border border-clinic-100 bg-clinic-50 p-5">
            <MapPin className="mt-0.5 h-5 w-5 shrink-0 text-clinic-700" aria-hidden="true" />
            <div><h2 className="font-semibold text-slate-950">Region reporting limitation</h2><p className="mt-2 text-sm leading-6 text-slate-700">{concernReport.issues.map((issue) => ISSUE_MESSAGES[issue] || "Region information is limited for this report.").join(" ")}</p></div>
          </aside>
        ) : null}

        <section aria-labelledby="limitations-heading">
          <h2 id="limitations-heading" className="text-2xl font-bold text-slate-950">Important limitations</h2>
          <ul className="mt-5 grid gap-3 sm:grid-cols-2">
            {concernReport.limitations.map((limitation) => <li key={limitation} className="flex items-start gap-3 border-b border-slate-200 pb-3 text-sm leading-6 text-slate-700"><BrainCircuit className="mt-1 h-4 w-4 shrink-0 text-brand-700" aria-hidden="true" />{limitation}</li>)}
          </ul>
        </section>

        <div className="flex items-start gap-3 rounded-lg border border-leaf-200 bg-leaf-50 p-5">
          <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-leaf-700" aria-hidden="true" />
          <p className="text-sm leading-6 text-slate-700">Questionnaire oiliness and dryness can provide context, but do not override uncertain image evidence. Sensitivity and allergies are never inferred from redness.</p>
        </div>
        <aside className="rounded-lg border border-slate-200 bg-white p-5 text-sm leading-6 text-slate-700 shadow-sm">
          <p>
            DermaScan AI identifies common visible facial characteristics for general skincare guidance. It does not diagnose acne, rosacea, pigmentation disorders, infections, allergies, or other medical conditions.
          </p>
          <p className="mt-2 font-semibold text-slate-900">
            Consult a qualified dermatologist for severe, painful, persistent, infected, rapidly changing, or unusual skin concerns.
          </p>
        </aside>
        <DisclaimerBox title="Visible observations are not diagnoses" />
        <ErrorMessage id="concern-action-error" message={actionError || error} />
        <div className="flex flex-col gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:justify-between">
          <SecondaryButton type="button" icon={UploadCloud} onClick={handleUploadAnother} disabled={isDeleting}>{isDeleting ? "Removing Image..." : "Upload a Clearer Image"}</SecondaryButton>
          <PrimaryButton type="button" icon={ArrowRight} onClick={() => navigate(concernReport.next_route || ROUTES.productEligibility)}>Check Product Eligibility</PrimaryButton>
        </div>
      </div>
    </section>
  );
}
