import { AlertTriangle, ArrowLeft, ArrowRight, MessageSquareText, Moon, RefreshCcw, ShieldCheck, Sun } from "lucide-react";
import { useEffect, useRef } from "react";
import DisclaimerBox from "../components/DisclaimerBox";
import ErrorMessage from "../components/ErrorMessage";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import { ROUTES, ROUTINE_GENERATION_STAGES } from "../constants/appContent";
import { useSkincareRoutine } from "../context/SkincareRoutineContext";


function RoutineTimeline({ title, icon: Icon, steps }) {
  return <section className="border-y border-slate-200 py-6" aria-labelledby={`${title}-heading`}>
    <div className="flex items-center gap-3"><Icon className="h-5 w-5 text-brand-700" aria-hidden="true" /><h2 id={`${title}-heading`} className="text-xl font-bold text-slate-950">{title}</h2></div>
    <ol className="mt-5 space-y-5">{steps.map((step) => <li key={`${title}-${step.step_number}`} className="grid grid-cols-[2rem_1fr] gap-4 break-inside-avoid">
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-sm font-bold text-white">{step.step_number}</span>
      <div><div className="flex flex-wrap items-center gap-2"><h3 className="font-semibold text-slate-950">{step.product_name}</h3>{step.is_optional ? <span className="rounded-md bg-amber-100 px-2 py-1 text-xs font-bold text-amber-900">Optional</span> : null}{step.is_demo_product ? <span className="rounded-md bg-clinic-100 px-2 py-1 text-xs font-bold text-clinic-900">Demo</span> : null}</div><p className="mt-1 text-sm font-medium text-brand-700">{step.category} · {step.brand_name}</p><p className="mt-2 text-sm leading-6 text-slate-700">{step.purpose}</p><p className="mt-1 text-sm leading-6 text-slate-600">{step.usage_guidance}</p>{step.cautions.length ? <p className="mt-2 text-sm text-amber-900">Caution: {step.cautions.join(" ")}</p> : null}</div>
    </li>)}</ol>
  </section>;
}


export default function SkincareRoutinePage() {
  const startedRef = useRef(false);
  const { routineReport, isGenerating, generationProgress, error, generateCurrentRoutine } = useSkincareRoutine();
  useEffect(() => {
    if (!routineReport && !isGenerating && !error && !startedRef.current) { startedRef.current = true; generateCurrentRoutine().catch(() => {}); }
  }, [routineReport, isGenerating, error, generateCurrentRoutine]);
  if (isGenerating && !routineReport) return <section className="px-4 py-14"><PageHeader eyebrow="Deterministic routine planning" title="Preparing Morning and Night Steps" description="Using only the eligible products selected by the recommendation report." /><div className="mx-auto max-w-3xl border-y border-slate-200 py-7" role="status"><div className="h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full bg-brand-600 transition-all" style={{ width: `${generationProgress}%` }} /></div><ol className="mt-6 grid gap-3 sm:grid-cols-2">{ROUTINE_GENERATION_STAGES.map((stage) => <li key={stage} className="text-sm font-medium text-slate-700">{stage}</li>)}</ol></div></section>;
  if (!routineReport) return <section className="px-4 py-14"><PageHeader eyebrow="Routine unavailable" title="The Routine Could Not Be Prepared Safely" /><div className="mx-auto max-w-3xl text-center"><ErrorMessage message={error} /><PrimaryButton className="mt-5" icon={RefreshCcw} onClick={() => generateCurrentRoutine().catch(() => {})}>Try Again</PrimaryButton></div></section>;
  return <section className="px-4 py-14 sm:px-6 lg:px-8"><PageHeader eyebrow="General skincare guidance" title="Your Morning and Night Routine" description="Ordered from your eligible recommendations using deterministic category rules." /><div className="mx-auto max-w-6xl space-y-8">
    <div className="flex items-start gap-3 border-y border-brand-200 bg-brand-50 px-4 py-5"><ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-brand-700" aria-hidden="true" /><p className="text-sm leading-6 text-slate-700">This routine is not a prescription. Follow current product labels, introduce products gradually, and do not use products that conflict with known allergies.</p></div>
    {routineReport.warnings.length ? <div className="flex items-start gap-3 bg-amber-50 p-4 text-sm text-amber-950"><AlertTriangle className="h-5 w-5 shrink-0" aria-hidden="true" /><p>{routineReport.warnings.join(" ")}</p></div> : null}
    <div className="grid gap-8 lg:grid-cols-2"><RoutineTimeline title="Morning Routine" icon={Sun} steps={routineReport.morning_routine} /><RoutineTimeline title="Night Routine" icon={Moon} steps={routineReport.night_routine} /></div>
    {routineReport.optional_products.length ? <section><h2 className="text-xl font-bold text-slate-950">Alternatives</h2><div className="mt-4 grid gap-4 md:grid-cols-2">{routineReport.optional_products.map((item) => <article key={item.product_id} className="rounded-lg border border-slate-200 bg-white p-4"><h3 className="font-semibold text-slate-950">{item.product_name}</h3><p className="mt-1 text-sm text-slate-600">{item.brand_name} · {item.category}</p><p className="mt-3 text-sm text-slate-700">{item.guidance}</p></article>)}</div></section> : null}
    <DisclaimerBox title="Routine guidance is not medical advice" />
    <div className="flex flex-col gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:flex-wrap sm:justify-between"><SecondaryButton to={ROUTES.productRecommendations} icon={ArrowLeft}>Review Recommendations</SecondaryButton><SecondaryButton to={ROUTES.feedback} state={{ routineReportId: routineReport.routine_report_id, feedbackCategory: "routine_feedback" }} icon={MessageSquareText}>Routine Feedback</SecondaryButton><PrimaryButton to={ROUTES.finalReport} icon={ArrowRight}>Generate Final Report</PrimaryButton></div>
  </div></section>;
}
