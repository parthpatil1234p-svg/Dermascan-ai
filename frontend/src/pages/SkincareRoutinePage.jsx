import { AlertTriangle, ArrowLeft, ArrowRight, MessageSquareText, Moon, RefreshCcw, ShieldCheck, Sparkles, Sun, Zap } from "lucide-react";
import { useEffect, useRef } from "react";
import DisclaimerBox from "../components/DisclaimerBox";
import ErrorMessage from "../components/ErrorMessage";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import Card3D from "../components/Card3D";
import { ROUTES, ROUTINE_GENERATION_STAGES } from "../constants/appContent";
import { useSkincareRoutine } from "../context/SkincareRoutineContext";

function RoutineTimeline({ title, icon: Icon, steps, glowColor = "emerald" }) {
  const isMorning = title.toLowerCase().includes("morning");
  return (
    <Card3D glowColor={glowColor} className="h-full border border-white/10 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-2xl">
      <div className="flex items-center gap-3 border-b border-white/10 pb-5">
        <div className={`flex h-11 w-11 items-center justify-center rounded-2xl ${isMorning ? "bg-amber-500/20 text-amber-400 border border-amber-500/30 shadow-md shadow-amber-500/10" : "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 shadow-md shadow-indigo-500/10"}`}>
          <Icon className="h-6 w-6" aria-hidden="true" />
        </div>
        <div>
          <h2 className="text-xl font-black text-white">{title}</h2>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {isMorning ? "Protect & Hydrate" : "Repair & Barrier Recovery"}
          </span>
        </div>
      </div>

      <ol className="mt-6 space-y-6">
        {steps.map((step) => (
          <li key={`${title}-${step.step_number}`} className="grid grid-cols-[2.5rem_1fr] gap-4">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 text-sm font-black text-slate-950 shadow-md shadow-emerald-500/20">
              0{step.step_number}
            </span>
            <div className="rounded-2xl border border-white/5 bg-slate-950/60 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-bold text-sm text-white">{step.product_name}</h3>
                {step.is_optional ? <span className="rounded-full bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 text-[10px] font-bold text-amber-300">Optional</span> : null}
                {step.is_demo_product ? <span className="rounded-full bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 text-[10px] font-bold text-cyan-300">Demo</span> : null}
              </div>
              <p className="mt-1 text-xs font-semibold text-emerald-400">{step.category.toUpperCase()} · {step.brand_name}</p>
              <p className="mt-2 text-xs leading-relaxed text-slate-300">{step.purpose}</p>
              <p className="mt-1 text-xs leading-relaxed text-slate-400 italic">{step.usage_guidance}</p>
              {step.cautions.length ? <p className="mt-2 rounded-lg bg-amber-950/40 border border-amber-500/30 p-2 text-xs text-amber-300">⚠️ Caution: {step.cautions.join(" ")}</p> : null}
            </div>
          </li>
        ))}
      </ol>
    </Card3D>
  );
}

export default function SkincareRoutinePage() {
  const startedRef = useRef(false);
  const { routineReport, isGenerating, generationProgress, error, generateCurrentRoutine } = useSkincareRoutine();

  useEffect(() => {
    if (!routineReport && !isGenerating && !error && !startedRef.current) {
      startedRef.current = true;
      generateCurrentRoutine().catch(() => {});
    }
  }, [routineReport, isGenerating, error, generateCurrentRoutine]);

  if (isGenerating && !routineReport) {
    return (
      <section className="relative min-h-screen bg-slate-950 px-4 py-16 text-white">
        <PageHeader eyebrow="Algorithmic Routine Synthesis" title="Generating 3D Morning & Night Steps" description="Using verified compatibility matrix and Step 11 safety exclusions." />
        <div className="mx-auto max-w-3xl rounded-3xl border border-white/10 bg-slate-900/80 p-8 shadow-2xl backdrop-blur-2xl" role="status">
          <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
            <span>Optimization Progress</span>
            <span className="text-emerald-400">{generationProgress}%</span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-slate-950 border border-white/5">
            <div className="h-full bg-gradient-to-r from-emerald-400 to-cyan-400 transition-all duration-300" style={{ width: `${generationProgress}%` }} />
          </div>
          <ol className="mt-8 grid gap-3 sm:grid-cols-2">
            {ROUTINE_GENERATION_STAGES.map((stage) => (
              <li key={stage} className="flex items-center gap-2.5 text-xs font-semibold text-slate-300">
                <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
                {stage}
              </li>
            ))}
          </ol>
        </div>
      </section>
    );
  }

  if (!routineReport) {
    return (
      <section className="relative min-h-screen bg-slate-950 px-4 py-16 text-white">
        <PageHeader eyebrow="Routine Synthesis Offline" title="The Routine Could Not Be Prepared Safely" />
        <div className="mx-auto max-w-3xl rounded-3xl border border-white/10 bg-slate-900/80 p-8 text-center backdrop-blur-2xl">
          <ErrorMessage message={error} />
          <PrimaryButton className="mt-6" icon={RefreshCcw} onClick={() => generateCurrentRoutine().catch(() => {})}>
            Regenerate Routine
          </PrimaryButton>
        </div>
      </section>
    );
  }

  return (
    <section className="relative min-h-screen bg-slate-950 px-4 py-14 text-slate-100 sm:px-6 lg:px-8">
      <PageHeader eyebrow="Personalized Dermatological Protocol" title="Your 3D Morning & Night Skincare Routine" description="Ordered sequentially by formulation density and active ingredient synergy." />

      <div className="mx-auto max-w-6xl space-y-8">
        <div className="flex items-start gap-3 rounded-2xl border border-emerald-500/30 bg-emerald-950/40 p-5 shadow-lg backdrop-blur-xl">
          <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" aria-hidden="true" />
          <p className="text-xs sm:text-sm leading-relaxed text-slate-300">
            This routine is general cosmetic guidance. Introduce active formulas gradually (2-3 times/week initially), do a 24-hour patch test on the inner forearm, and discontinue if persistent erythema occurs.
          </p>
        </div>

        {routineReport.warnings.length ? (
          <div className="flex items-start gap-3 rounded-2xl border border-amber-500/30 bg-amber-950/40 p-4 text-xs sm:text-sm text-amber-300">
            <AlertTriangle className="h-5 w-5 shrink-0 text-amber-400" aria-hidden="true" />
            <p>{routineReport.warnings.join(" ")}</p>
          </div>
        ) : null}

        <div className="grid gap-8 lg:grid-cols-2">
          <RoutineTimeline title="Morning Routine" icon={Sun} steps={routineReport.morning_routine} glowColor="emerald" />
          <RoutineTimeline title="Night Routine" icon={Moon} steps={routineReport.night_routine} glowColor="violet" />
        </div>

        {routineReport.optional_products.length ? (
          <section className="space-y-4">
            <h2 className="text-xl font-bold text-white">Compatible Alternatives</h2>
            <div className="grid gap-4 md:grid-cols-2">
              {routineReport.optional_products.map((item) => (
                <Card3D key={item.product_id} glowColor="cyan" className="border-white/10 bg-slate-900/80 p-5 backdrop-blur-xl">
                  <h3 className="font-bold text-sm text-white">{item.product_name}</h3>
                  <p className="mt-1 text-xs font-semibold text-cyan-400">{item.brand_name} · {item.category}</p>
                  <p className="mt-2 text-xs text-slate-300 leading-relaxed">{item.guidance}</p>
                </Card3D>
              ))}
            </div>
          </section>
        ) : null}

        <DisclaimerBox title="Routine guidance is not medical advice" />

        <div className="flex flex-col gap-3 border-t border-white/10 pt-6 sm:flex-row sm:flex-wrap sm:justify-between">
          <SecondaryButton to={ROUTES.productRecommendations} icon={ArrowLeft}>
            Review Recommendations
          </SecondaryButton>
          <SecondaryButton
            to={ROUTES.feedback}
            state={{ routineReportId: routineReport.routine_report_id, feedbackCategory: "routine_feedback" }}
            icon={MessageSquareText}
          >
            Routine Feedback
          </SecondaryButton>
          <PrimaryButton to={ROUTES.finalReport} icon={ArrowRight}>
            Generate Final Report
          </PrimaryButton>
        </div>
      </div>
    </section>
  );
}

