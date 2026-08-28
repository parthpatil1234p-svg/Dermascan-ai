import {
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  ClipboardPenLine,
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
import { ROUTES, SKIN_TYPE_ANALYSIS_STAGES } from "../constants/appContent";
import { useFaceDetection } from "../context/FaceDetectionContext";
import { useImagePreprocessing } from "../context/ImagePreprocessingContext";
import { useImageQuality } from "../context/ImageQualityContext";
import { useSkinType } from "../context/SkinTypeContext";
import { useUpload } from "../context/UploadContext";

function AnalysisProgress({ progress }) {
  const activeIndex = Math.min(
    SKIN_TYPE_ANALYSIS_STAGES.length - 1,
    Math.floor((progress / 100) * SKIN_TYPE_ANALYSIS_STAGES.length),
  );

  return (
    <div className="mx-auto max-w-3xl border-y border-slate-200 py-8" role="status">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-950">
            Estimating broad visible skin behavior
          </h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            The validated model is reviewing the private prepared image and comparing its confidence with your questionnaire.
          </p>
        </div>
        <span className="text-lg font-bold text-brand-700">{progress}%</span>
      </div>
      <div
        className="mt-5 h-2 overflow-hidden rounded-full bg-slate-200"
        role="progressbar"
        aria-label="Skin-type analysis progress"
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
        {SKIN_TYPE_ANALYSIS_STAGES.map((stage, index) => (
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

function ProbabilityBar({ label, value }) {
  return (
    <div>
      <div className="flex items-center justify-between gap-4 text-sm">
        <span className="font-semibold text-slate-800">{label}</span>
        <span className="font-bold text-slate-950">{value}%</span>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-brand-600"
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
    </div>
  );
}

function sensitivityLabel(value) {
  if (value === true) return "Yes";
  if (value === false) return "No";
  return "Not sure";
}

export default function SkinTypeAnalysisPage() {
  const navigate = useNavigate();
  const startedRef = useRef(false);
  const [actionError, setActionError] = useState("");
  const {
    skinTypeReport,
    modelStatus,
    isCheckingModel,
    isAnalyzing,
    analysisProgress,
    error,
    checkModelReadiness,
    analyzeCurrentImage,
    clearSkinTypeState,
  } = useSkinType();
  const { clearPreprocessingState } = useImagePreprocessing();
  const { clearFaceDetectionState } = useFaceDetection();
  const { clearQualityState } = useImageQuality();
  const {
    isDeleting,
    deleteCurrentUpload,
    clearUploadReference,
  } = useUpload();

  useEffect(() => {
    if (skinTypeReport || isCheckingModel || isAnalyzing || error || startedRef.current) {
      return;
    }
    startedRef.current = true;
    const start = async () => {
      const status = await checkModelReadiness();
      if (status.loaded) await analyzeCurrentImage();
    };
    start().catch(() => {});
  }, [
    skinTypeReport,
    isCheckingModel,
    isAnalyzing,
    error,
    checkModelReadiness,
    analyzeCurrentImage,
  ]);

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

  if ((isCheckingModel || isAnalyzing) && !skinTypeReport) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader
          eyebrow="Skin type estimation"
          title={isCheckingModel ? "Checking Model Readiness" : "Reviewing Skin Behavior"}
          description="This uses the exported four-class model and your self-reported skin behavior. It does not diagnose a condition."
        />
        {isCheckingModel ? (
          <div className="mx-auto max-w-3xl border-y border-slate-200 py-10 text-center" role="status">
            <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
            <p className="mt-4 text-sm font-semibold text-slate-700">
              Verifying model files and input compatibility...
            </p>
          </div>
        ) : (
          <AnalysisProgress progress={analysisProgress} />
        )}
      </section>
    );
  }

  if (modelStatus && !modelStatus.loaded) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader
          eyebrow="Model unavailable"
          title="Skin Type Analysis Is Not Ready"
          description="A validated, compatible model artifact has not been installed on this backend. No estimate has been generated."
        />
        <div className="mx-auto max-w-3xl space-y-6">
          <div className="flex items-start gap-4 border-y border-amber-200 bg-amber-50 px-4 py-7">
            <AlertTriangle className="mt-0.5 h-6 w-6 shrink-0 text-amber-700" aria-hidden="true" />
            <div>
              <h2 className="font-semibold text-slate-950">Validated model required</h2>
              <p className="mt-2 text-sm leading-6 text-slate-700">
                Add artifacts produced by the documented training, evaluation, and export pipeline. DermaScan AI will not substitute demo probabilities.
              </p>
            </div>
          </div>
          <ErrorMessage id="skin-type-action-error" message={actionError || error} />
          <div className="flex flex-col gap-3 sm:flex-row sm:justify-between">
            <SecondaryButton type="button" icon={UploadCloud} onClick={handleUploadAnother} disabled={isDeleting}>
              Upload Another Image
            </SecondaryButton>
            <PrimaryButton type="button" icon={RefreshCcw} onClick={handleRetry} disabled={isCheckingModel}>
              Check Again
            </PrimaryButton>
          </div>
        </div>
      </section>
    );
  }

  if (!skinTypeReport) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader
          eyebrow="Analysis unavailable"
          title="We Could Not Estimate Skin Type"
          description="No medical diagnosis, skin-concern detection, or product recommendation was performed."
        />
        <div className="mx-auto max-w-3xl border-y border-slate-200 py-8 text-center">
          <ErrorMessage id="skin-type-error" message={error || actionError} />
          <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
            <SecondaryButton type="button" icon={UploadCloud} onClick={handleUploadAnother} disabled={isDeleting}>
              Upload Another Image
            </SecondaryButton>
            <PrimaryButton type="button" icon={RefreshCcw} onClick={handleRetry} disabled={isAnalyzing}>
              Try Again
            </PrimaryButton>
          </div>
        </div>
      </section>
    );
  }

  const uncertain = skinTypeReport.result_status === "uncertain";
  const probabilities = Object.entries(skinTypeReport.probabilities).sort(
    ([, left], [, right]) => right - left,
  );

  return (
    <section className="px-4 py-14 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="Broad skin type estimate"
        title={uncertain ? "Skin Type Result: Uncertain" : `Estimated Skin Type: ${skinTypeReport.skin_type}`}
        description="This result combines model probabilities with your questionnaire without hiding low confidence or disagreement."
      />
      <div className="mx-auto max-w-6xl space-y-10">
        <DemoModeNotice visible={skinTypeReport.analysis_mode === "demonstration"} />
        <section className="grid gap-6 border-y border-slate-200 py-8 lg:grid-cols-[16rem_1fr] lg:items-center">
          <div className="text-center lg:text-left">
            <p className="text-sm font-semibold text-slate-600">Model confidence</p>
            <p className="mt-2 text-4xl font-bold text-slate-950">{skinTypeReport.confidence}%</p>
            <p className="mt-1 text-sm font-semibold text-brand-700">{skinTypeReport.confidence_level}</p>
          </div>
          <div className={`rounded-lg border p-5 ${uncertain ? "border-amber-200 bg-amber-50" : "border-leaf-200 bg-leaf-50"}`}>
            <div className="flex items-start gap-3">
              {uncertain ? (
                <AlertTriangle className="mt-0.5 h-6 w-6 shrink-0 text-amber-700" aria-hidden="true" />
              ) : (
                <CheckCircle2 className="mt-0.5 h-6 w-6 shrink-0 text-leaf-700" aria-hidden="true" />
              )}
              <div>
                <h2 className="text-lg font-semibold text-slate-950">
                  {uncertain ? "No class was forced" : `${skinTypeReport.skin_type} characteristics estimated`}
                </h2>
                <p className="mt-2 text-sm leading-6 text-slate-700">{skinTypeReport.explanation}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-8 lg:grid-cols-2">
          <div>
            <h2 className="text-2xl font-bold text-slate-950">Model probabilities</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              These values describe model output, not medical certainty.
            </p>
            <div className="mt-6 space-y-5">
              {probabilities.map(([label, value]) => (
                <ProbabilityBar key={label} label={label} value={value} />
              ))}
            </div>
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-950">Questionnaire comparison</h2>
            <dl className="mt-6 grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <dt className="text-sm font-semibold text-slate-600">Agreement</dt>
                <dd className="mt-1 text-xl font-bold text-slate-950">{skinTypeReport.agreement}</dd>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <dt className="text-sm font-semibold text-slate-600">Self-reported sensitivity</dt>
                <dd className="mt-1 text-xl font-bold text-slate-950">
                  {sensitivityLabel(skinTypeReport.self_reported_sensitivity)}
                </dd>
              </div>
            </dl>
            <div className="mt-5 flex items-start gap-3 rounded-lg border border-clinic-100 bg-clinic-50 p-5">
              <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-clinic-700" aria-hidden="true" />
              <p className="text-sm leading-6 text-slate-700">
                Skin sensitivity is based primarily on your self-reported information. It is not confirmed from the facial image.
              </p>
            </div>
          </div>
        </section>

        <section aria-labelledby="limitations-heading">
          <h2 id="limitations-heading" className="text-2xl font-bold text-slate-950">Limitations</h2>
          <ul className="mt-5 grid gap-3 sm:grid-cols-2">
            {skinTypeReport.limitations.map((limitation) => (
              <li key={limitation} className="flex items-start gap-3 border-b border-slate-200 pb-3 text-sm leading-6 text-slate-700">
                <BrainCircuit className="mt-1 h-4 w-4 shrink-0 text-brand-700" aria-hidden="true" />
                {limitation}
              </li>
            ))}
          </ul>
        </section>

        <DisclaimerBox title="General skincare estimate only" />
        <p className="text-sm leading-6 text-slate-600">
          For severe, painful, infected, persistent, or unusual skin concerns, consult a qualified dermatologist.
        </p>
        <ErrorMessage id="skin-type-action-error" message={actionError || error} />

        <div className="flex flex-col gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:justify-between">
          <SecondaryButton type="button" icon={UploadCloud} onClick={handleUploadAnother} disabled={isDeleting}>
            {isDeleting ? "Removing Image..." : "Upload a Clearer Image"}
          </SecondaryButton>
          <div className="flex flex-col gap-3 sm:flex-row">
            {uncertain ? (
              <SecondaryButton type="button" icon={ClipboardPenLine} onClick={() => navigate(ROUTES.skinProfile)}>
                Review Skin Profile
              </SecondaryButton>
            ) : null}
            <PrimaryButton
              type="button"
              icon={ArrowRight}
              onClick={() => navigate(skinTypeReport.next_route || ROUTES.skinConcernAnalysis)}
            >
              {uncertain ? "Continue with General Guidance" : "Continue to Concern Analysis"}
            </PrimaryButton>
          </div>
        </div>
      </div>
    </section>
  );
}
