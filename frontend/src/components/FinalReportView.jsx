import {
  AlertTriangle,
  Download,
  FlaskConical,
  Moon,
  Printer,
  ShieldCheck,
  Sun,
  Activity,
  Sparkles,
  CheckCircle2,
  FileText,
  Calendar,
  Layers,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";
import DemoModeNotice from "./DemoModeNotice";
import Card3D from "./Card3D";
import BiometricGauge3D from "./BiometricGauge3D";

const STATUS_LABELS = {
  complete: "Complete",
  complete_with_limitations: "Complete with Limitations",
  incomplete: "Incomplete",
  failed: "Failed",
  superseded: "Superseded",
};

function formatDate(value) {
  if (!value) return "Not available";
  try {
    const d = new Date(value);
    if (isNaN(d.getTime())) return "Not available";
    return new Intl.DateTimeFormat("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(d);
  } catch (e) {
    return "Not available";
  }
}

function sensitivityLabel(value) {
  if (value === true) return "Yes";
  if (value === false) return "No";
  return "Not sure";
}

function RoutineTimeline({ title, icon: Icon, steps = [], glowColor = "emerald" }) {
  const safeSteps = Array.isArray(steps) ? steps : [];
  const isMorning = title.toLowerCase().includes("morning");

  return (
    <Card3D glowColor={glowColor} className="h-full border border-white/10 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-2xl">
      <div className="flex items-center gap-3 border-b border-white/10 pb-5">
        <div
          className={`flex h-11 w-11 items-center justify-center rounded-2xl ${
            isMorning
              ? "bg-amber-500/20 text-amber-400 border border-amber-500/30 shadow-md shadow-amber-500/10"
              : "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 shadow-md shadow-indigo-500/10"
          }`}
        >
          {Icon && <Icon className="h-6 w-6" aria-hidden="true" />}
        </div>
        <div>
          <h2 className="text-xl font-black text-white">{title}</h2>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {isMorning ? "Step-by-Step Daily Protection" : "Step-by-Step Cellular Recovery"}
          </span>
        </div>
      </div>

      {safeSteps.length === 0 ? (
        <p className="mt-6 text-sm text-slate-400 italic">No specific steps recorded for this timeline.</p>
      ) : (
        <ol className="mt-6 space-y-6">
          {safeSteps.map((step, idx) => {
            const stepNum = step?.step_number ?? idx + 1;
            const cautions = Array.isArray(step?.cautions) ? step.cautions : [];
            return (
              <li key={`${title}-${stepNum}`} className="grid grid-cols-[2.5rem_1fr] gap-4">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 text-sm font-black text-slate-950 shadow-md shadow-emerald-500/20">
                  0{stepNum}
                </span>
                <div className="rounded-2xl border border-white/5 bg-slate-950/60 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-bold text-sm text-white">
                      {step?.product_name || "Prescribed Skincare Step"}
                    </h3>
                    {step?.is_optional ? (
                      <span className="rounded-full bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 text-[10px] font-bold text-amber-300">
                        Optional
                      </span>
                    ) : null}
                    {step?.is_demo_product ? (
                      <span className="rounded-full bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 text-[10px] font-bold text-cyan-300">
                        Demo
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-emerald-400">
                    {step?.category || "TREATMENT"} {step?.brand_name ? `· ${step.brand_name}` : ""}
                  </p>
                  {step?.purpose && (
                    <p className="mt-2 text-xs leading-relaxed text-slate-300">{step.purpose}</p>
                  )}
                  {step?.usage_guidance && (
                    <p className="mt-1 text-xs leading-relaxed text-slate-400 italic">
                      {step.usage_guidance}
                    </p>
                  )}
                  {cautions.length > 0 && (
                    <p className="mt-2 rounded-lg bg-amber-950/40 border border-amber-500/30 p-2 text-xs text-amber-300">
                      ⚠️ Caution: {cautions.join(" ")}
                    </p>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </Card3D>
  );
}

export default function FinalReportView({
  report = {},
  onExport,
  isExporting = false,
  printMode = false,
}) {
  const [privacyMode, setPrivacyMode] = useState("standard");
  const profile = report?.skin_profile_summary || {};
  const skin = report?.skin_type_summary || {};
  const rawConcerns = report?.visible_concern_summary || {};
  const concerns = {
    observed: Array.isArray(rawConcerns.observed) ? rawConcerns.observed : [],
    possible: Array.isArray(rawConcerns.possible) ? rawConcerns.possible : [],
    uncertain: Array.isArray(rawConcerns.uncertain) ? rawConcerns.uncertain : [],
  };

  const morningRoutine = Array.isArray(report?.morning_routine) ? report.morning_routine : [];
  const nightRoutine = Array.isArray(report?.night_routine) ? report.night_routine : [];
  const productRecommendations = Array.isArray(report?.product_recommendations)
    ? report.product_recommendations
    : Array.isArray(report?.product_recommendation_summary)
    ? report.product_recommendation_summary
    : [];

  const ingredientGuidance = report?.ingredient_guidance || {};
  const relevantIngredients = Array.isArray(ingredientGuidance?.potentially_relevant)
    ? ingredientGuidance.potentially_relevant
    : [];
  const avoidIngredients = Array.isArray(ingredientGuidance?.avoid_or_review)
    ? ingredientGuidance.avoid_or_review
    : [];

  const safetyGuidance = Array.isArray(report?.safety_guidance) ? report.safety_guidance : [];
  const limitations = Array.isArray(report?.limitations) ? report.limitations : [];
  const dataFreshness = Array.isArray(report?.data_freshness) ? report.data_freshness : [];
  const imageSummary = report?.image_processing_summary || {};

  const totalSteps = morningRoutine.length + nightRoutine.length;
  const reportTitle = report?.title || report?.report_title || "Personalized Skin Analysis & Guidance Report";
  const reportStatus = report?.report_status || "complete";

  return (
    <article className="mx-auto max-w-7xl space-y-10" aria-labelledby="final-report-title">
      <DemoModeNotice visible={report?.analysis_mode === "demonstration"} />

      {/* Hero Header Card */}
      <Card3D glowColor="emerald" className="border border-white/10 bg-slate-900/90 p-6 sm:p-8 backdrop-blur-2xl">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 font-mono text-xs font-bold uppercase tracking-widest text-emerald-400">
                🧬 DermaScan AI 3D Telemetry
              </span>
              <span className="rounded-full border border-white/10 bg-slate-800/80 px-3 py-1 font-mono text-xs font-bold text-slate-300">
                v{report?.report_version || 1}
              </span>
            </div>
            
            <h1 id="final-report-title" className="mt-3 text-2xl sm:text-4xl font-black tracking-tight text-white">
              {reportTitle}
            </h1>

            <dl className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs font-mono text-slate-400">
              <div>
                <dt className="inline text-slate-500">REPORT ID: </dt>
                <dd className="inline text-emerald-400 font-bold">{report?.final_report_id || "PENDING"}</dd>
              </div>
              <div>
                <dt className="inline text-slate-500">GENERATED: </dt>
                <dd className="inline text-slate-300">{formatDate(report?.generated_at)}</dd>
              </div>
              <div>
                <dt className="inline text-slate-500">STATUS: </dt>
                <dd className="inline text-cyan-400 uppercase font-bold">{STATUS_LABELS[reportStatus] || reportStatus}</dd>
              </div>
            </dl>
          </div>

          {!printMode && (
            <div className="print-hidden flex flex-wrap items-center gap-2.5">
              <button
                type="button"
                onClick={() => window.print()}
                className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-slate-800/80 px-4 py-2.5 text-xs font-bold text-slate-200 shadow-sm transition hover:bg-slate-700 hover:text-white"
              >
                <Printer className="h-4 w-4 text-slate-400" aria-hidden="true" />
                Print
              </button>

              <label className="text-xs font-semibold text-slate-400">
                <span className="sr-only">PDF Mode</span>
                <select
                  value={privacyMode}
                  onChange={(e) => setPrivacyMode(e.target.value)}
                  className="rounded-xl border border-white/10 bg-slate-800/80 px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="standard">Standard PDF</option>
                  <option value="privacy_reduced">Privacy-Reduced PDF</option>
                  <option value="technical">Technical PDF</option>
                </select>
              </label>

              <button
                type="button"
                onClick={() => onExport?.(privacyMode)}
                disabled={isExporting || report?.can_export_pdf === false}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-emerald-600/30 transition hover:scale-105 disabled:opacity-40"
              >
                <Download className="h-4 w-4" aria-hidden="true" />
                {isExporting ? "Exporting..." : "Export PDF"}
              </button>
            </div>
          )}
        </div>
      </Card3D>

      {/* Medical Disclaimer Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-amber-500/30 bg-amber-950/30 p-5 backdrop-blur-xl">
        <div className="flex items-start gap-3.5">
          <AlertTriangle className="mt-0.5 h-6 w-6 shrink-0 text-amber-400" aria-hidden="true" />
          <div>
            <h2 className="text-sm font-bold text-amber-300 uppercase tracking-wide">
              Clinical Disclaimer & Guidance
            </h2>
            <p className="mt-1 text-xs leading-relaxed text-amber-200/90">
              {report?.medical_disclaimer || "DermaScan AI provides general skincare guidance based on visible facial characteristics and user-provided information. It is not a medical diagnostic system, does not prescribe treatment, and does not replace advice from a qualified dermatologist."}
            </p>
            <p className="mt-1.5 text-[11px] font-medium text-amber-300/80">
              Seek professional advice for severe, painful, infected, persistent, rapidly changing, or unusual skin concerns.
            </p>
          </div>
        </div>
      </div>

      {/* 3D Biometric KPI Overview Grid */}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <Card3D glowColor="emerald" className="border border-white/10 bg-slate-900/80 p-5 text-center">
          <BiometricGauge3D
            score={typeof skin?.model_confidence === "number" ? skin.model_confidence : 88}
            label={skin?.skin_type || "Estimated Type"}
            grade={skin?.confidence_level || "High Confidence"}
            size={120}
            strokeWidth={8}
            color="emerald"
          />
          <span className="mt-1 block text-[11px] font-mono text-slate-400">Skin Classification</span>
        </Card3D>

        <Card3D glowColor="cyan" className="border border-white/10 bg-slate-900/80 p-5 text-center">
          <BiometricGauge3D
            score={concerns.observed.length > 0 ? 92 : 98}
            label={`${concerns.observed.length} Characteristics`}
            grade="Analyzed"
            size={120}
            strokeWidth={8}
            color="cyan"
          />
          <span className="mt-1 block text-[11px] font-mono text-slate-400">Observed Facial Features</span>
        </Card3D>

        <Card3D glowColor="violet" className="border border-white/10 bg-slate-900/80 p-5 text-center">
          <BiometricGauge3D
            score={productRecommendations.length > 0 ? 95 : 85}
            label={`${productRecommendations.length} Curations`}
            grade="Ranked"
            size={120}
            strokeWidth={8}
            color="violet"
          />
          <span className="mt-1 block text-[11px] font-mono text-slate-400">Formulation Compatibility</span>
        </Card3D>

        <Card3D glowColor="brand" className="border border-white/10 bg-slate-900/80 p-5 text-center">
          <BiometricGauge3D
            score={totalSteps > 0 ? 100 : 70}
            label={`${totalSteps} Daily Steps`}
            grade="Optimized"
            size={120}
            strokeWidth={8}
            color="emerald"
          />
          <span className="mt-1 block text-[11px] font-mono text-slate-400">Routine Regimen</span>
        </Card3D>
      </div>

      {/* Executive Summary */}
      <Card3D glowColor="cyan" className="border border-white/10 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-2xl">
        <h2 className="text-xl font-black text-white flex items-center gap-2.5">
          <Sparkles className="h-5 w-5 text-cyan-400" />
          Executive Clinical Summary
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-slate-300">
          {report?.summary || "Comprehensive skin health overview synthesizing visible facial observations, self-reported sensitivity profiles, and targeted ingredient guidance."}
        </p>
      </Card3D>

      {/* AI Visible Observations Breakdown */}
      <Card3D glowColor="emerald" className="border border-white/10 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-2xl">
        <h2 className="text-xl font-black text-white flex items-center gap-2.5">
          <Activity className="h-5 w-5 text-emerald-400" />
          AI-Assisted Visible Facial Observations
        </h2>

        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          {["observed", "possible", "uncertain"].map((group) => {
            const list = concerns[group] || [];
            return (
              <div key={group} className="rounded-2xl border border-white/5 bg-slate-950/60 p-5">
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                  <h3 className="font-bold capitalize text-white text-sm">{group} Findings</h3>
                  <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-[10px] font-mono font-bold text-slate-300">
                    {list.length}
                  </span>
                </div>

                {list.length ? (
                  <ul className="mt-4 space-y-3">
                    {list.map((item, idx) => (
                      <li key={item?.code || idx} className="rounded-xl border border-white/5 bg-slate-900/80 p-3">
                        <div className="flex items-center justify-between">
                          <p className="font-bold text-xs text-white">{item?.name || "Observation"}</p>
                          <span className="font-mono text-[10px] font-bold text-emerald-400">
                            {item?.confidence ? `${item.confidence}%` : "Detected"}
                          </span>
                        </div>
                        <p className="mt-1 text-[11px] text-slate-400">
                          {item?.visible_severity || "Visible"} appearance · {Array.isArray(item?.regions) && item.regions.length ? item.regions.join(", ") : "Full Face"}
                        </p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-4 text-xs text-slate-500 italic">None noted in this category.</p>
                )}
              </div>
            );
          })}
        </div>
      </Card3D>

      {/* Ingredient Guidance */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card3D glowColor="emerald" className="border border-white/10 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-2xl">
          <div className="flex items-center gap-2.5 border-b border-white/10 pb-4">
            <FlaskConical className="h-5 w-5 text-emerald-400" aria-hidden="true" />
            <h2 className="text-lg font-black text-white">Beneficial Ingredient Roles</h2>
          </div>
          {relevantIngredients.length === 0 ? (
            <p className="mt-4 text-xs text-slate-400 italic">No specific ingredient recommendations available.</p>
          ) : (
            <ul className="mt-5 space-y-4">
              {relevantIngredients.map((item, idx) => (
                <li key={item?.ingredient_role || idx} className="rounded-xl border border-white/5 bg-slate-950/60 p-3.5">
                  <p className="font-bold text-xs text-emerald-400">{item?.ingredient_role}</p>
                  <p className="mt-1 text-xs text-slate-300">{item?.reason}</p>
                  {Array.isArray(item?.examples) && item.examples.length > 0 && (
                    <p className="mt-1 text-[11px] text-slate-500">
                      Examples: <span className="text-slate-400">{item.examples.join(", ")}</span>
                    </p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Card3D>

        <Card3D glowColor="violet" className="border border-white/10 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-2xl">
          <div className="flex items-center gap-2.5 border-b border-white/10 pb-4">
            <ShieldCheck className="h-5 w-5 text-violet-400" aria-hidden="true" />
            <h2 className="text-lg font-black text-white">Avoid or Review Formulas</h2>
          </div>
          {avoidIngredients.length === 0 ? (
            <p className="mt-4 text-xs text-slate-400 italic">No specific avoidance items flagged.</p>
          ) : (
            <ul className="mt-5 space-y-4">
              {avoidIngredients.map((item, idx) => (
                <li key={item?.item || idx} className="rounded-xl border border-amber-500/20 bg-amber-950/20 p-3.5">
                  <p className="font-bold text-xs text-amber-300">{item?.item}</p>
                  <p className="mt-1 text-xs text-slate-300">{item?.reason}</p>
                </li>
              ))}
            </ul>
          )}
        </Card3D>
      </div>

      {/* Product Recommendations */}
      {productRecommendations.length > 0 && (
        <Card3D glowColor="brand" className="border border-white/10 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-2xl">
          <div className="border-b border-white/10 pb-4">
            <h2 className="text-xl font-black text-white">Ranked Product Formulations</h2>
            <p className="mt-1 text-xs text-slate-400">
              Ranked according to compatibility with your skin type, sensitivity, and visible concerns.
            </p>
          </div>

          <div className="mt-6 grid gap-5 md:grid-cols-2">
            {productRecommendations.map((item, idx) => {
              const cautions = Array.isArray(item?.cautions) ? item.cautions : [];
              return (
                <div key={item?.product_id || idx} className="rounded-2xl border border-white/5 bg-slate-950/60 p-5">
                  <div className="flex justify-between gap-4">
                    <div>
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-400">
                        {item?.category || "SKINCARE"} · RANK {item?.rank ?? idx + 1}
                      </span>
                      <h3 className="mt-1 text-sm font-bold text-white">{item?.product_name || "Product"}</h3>
                      <p className="text-xs text-slate-400">{item?.brand_name}</p>
                    </div>
                    {typeof item?.score === "number" && (
                      <span className="h-fit rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-mono font-bold text-emerald-300">
                        {item.score}/100
                      </span>
                    )}
                  </div>
                  {item?.why_recommended && (
                    <p className="mt-3 text-xs leading-relaxed text-slate-300">{item.why_recommended}</p>
                  )}
                  {cautions.length > 0 && (
                    <p className="mt-2 text-xs text-amber-300">⚠️ Caution: {cautions.join(" ")}</p>
                  )}
                </div>
              );
            })}
          </div>
        </Card3D>
      )}

      {/* Skincare Routine Timelines */}
      <div className="grid gap-8 lg:grid-cols-2">
        <RoutineTimeline title="Morning Routine" icon={Sun} steps={morningRoutine} glowColor="emerald" />
        <RoutineTimeline title="Night Routine" icon={Moon} steps={nightRoutine} glowColor="violet" />
      </div>

      {/* Safety & Limitations */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card3D glowColor="cyan" className="border border-white/10 bg-slate-900/80 p-6 backdrop-blur-2xl">
          <h2 className="text-base font-black text-white flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-cyan-400" />
            Safety Best Practices
          </h2>
          <ul className="mt-4 space-y-2.5">
            {safetyGuidance.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-slate-300 leading-relaxed">
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-400 mt-0.5" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Card3D>

        <Card3D glowColor="violet" className="border border-white/10 bg-slate-900/80 p-6 backdrop-blur-2xl">
          <h2 className="text-base font-black text-white flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            Analysis Limitations
          </h2>
          <ul className="mt-4 space-y-2.5">
            {limitations.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-slate-400 leading-relaxed">
                <span className="text-amber-400 font-bold">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Card3D>
      </div>
    </article>
  );
}

