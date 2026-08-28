import {
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  CheckCircle2,
  ChevronDown,
  CircleHelp,
  Eye,
  Info,
  Layers3,
  MessageSquareText,
  RefreshCcw,
  ShieldCheck,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import DisclaimerBox from "../components/DisclaimerBox";
import ErrorMessage from "../components/ErrorMessage";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import { PRODUCT_RECOMMENDATION_STAGES, ROUTES } from "../constants/appContent";
import { displayCode } from "../constants/catalogueOptions";
import { useProductRecommendation } from "../context/ProductRecommendationContext";

const CONFIDENCE_STYLE = {
  high: "bg-leaf-100 text-leaf-900",
  moderate: "bg-amber-100 text-amber-950",
  low: "bg-slate-200 text-slate-800",
};

const SCORE_STYLE = {
  "Excellent Match": "bg-leaf-100 text-leaf-900",
  "Strong Match": "bg-brand-100 text-brand-900",
  "Good Match": "bg-clinic-100 text-clinic-900",
  "Moderate Match": "bg-amber-100 text-amber-950",
  "Low Match": "bg-slate-200 text-slate-800",
};

const BREAKDOWN_LABELS = {
  skin_type_match: "Skin-type match",
  visible_concern_match: "Visible-concern match",
  ingredient_relevance: "Ingredient relevance",
  sensitivity_compatibility: "Sensitivity compatibility",
  budget_fit: "Budget fit",
  availability: "Availability",
  brand_preference: "Brand preference",
  data_quality: "Catalogue data quality",
  rating: "Rating contribution",
};

function formatPrice(price) {
  if (!price) return "Price unavailable";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: price.currency,
    maximumFractionDigits: 2,
  }).format(price.amount);
}

function GenerationProgress({ progress }) {
  const activeIndex = Math.min(
    PRODUCT_RECOMMENDATION_STAGES.length - 1,
    Math.floor((progress / 100) * PRODUCT_RECOMMENDATION_STAGES.length),
  );
  return (
    <div className="mx-auto max-w-3xl border-y border-slate-200 py-8" role="status">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-950">Ranking eligible catalogue options</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Component scores and caution penalties are being calculated from stored project data.
          </p>
        </div>
        <span className="text-lg font-bold text-brand-700">{progress}%</span>
      </div>
      <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-200" role="progressbar" aria-label="Recommendation generation progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow={progress}>
        <div className="h-full rounded-full bg-brand-600 transition-all" style={{ width: `${progress}%` }} />
      </div>
      <ol className="mt-6 grid gap-3 sm:grid-cols-2">
        {PRODUCT_RECOMMENDATION_STAGES.map((stage, index) => (
          <li key={stage} className={`flex items-center gap-3 text-sm ${index <= activeIndex ? "font-semibold text-slate-900" : "text-slate-500"}`}>
            <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${index < activeIndex ? "bg-leaf-600" : index === activeIndex ? "animate-pulse bg-brand-600" : "bg-slate-300"}`} />
            {stage}
          </li>
        ))}
      </ol>
    </div>
  );
}

function ScoreBreakdown({ recommendation }) {
  const entries = Object.entries(BREAKDOWN_LABELS);
  return (
    <details className="mt-5 border-t border-slate-200 pt-4 group">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-semibold text-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600">
        <span className="inline-flex items-center gap-2"><BarChart3 className="h-4 w-4" aria-hidden="true" />View score breakdown</span>
        <ChevronDown className="h-4 w-4 transition group-open:rotate-180" aria-hidden="true" />
      </summary>
      <dl className="mt-4 grid gap-x-8 gap-y-3 sm:grid-cols-2">
        {entries.map(([key, label]) => (
          <div key={key} className="flex items-center justify-between gap-4 border-b border-slate-100 pb-2 text-sm">
            <dt className="text-slate-600">{label}</dt>
            <dd className="font-semibold text-slate-950">
              {key === "rating" && recommendation.score_breakdown[key] === 50
                ? "50 (Neutral)"
                : recommendation.score_breakdown[key]}
            </dd>
          </div>
        ))}
      </dl>
      <div className="mt-4 grid grid-cols-3 gap-3 border-y border-slate-200 py-3 text-center text-sm">
        <div><p className="text-slate-500">Base</p><p className="mt-1 font-bold text-slate-950">{recommendation.base_score}</p></div>
        <div><p className="text-slate-500">Penalty</p><p className="mt-1 font-bold text-amber-800">-{recommendation.caution_penalty}</p></div>
        <div><p className="text-slate-500">Final</p><p className="mt-1 font-bold text-brand-700">{recommendation.final_score}</p></div>
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-500">
        This is a project-specific relevance score, not a medical score or probability of success.
      </p>
    </details>
  );
}

function RecommendationCard({ item, onView, disabled }) {
  return (
    <article className="flex h-full flex-col rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase text-brand-700">
            {item.rank === 1 ? "Top Match" : `Recommended Option ${item.rank}`}
          </p>
          <h3 className="mt-1 text-lg font-bold text-slate-950">{item.product_name}</h3>
          <p className="mt-1 text-sm text-slate-600">{item.brand_name}</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-slate-950">{item.final_score}<span className="text-sm font-medium text-slate-500">/100</span></p>
          <span className={`mt-1 inline-flex rounded-md px-2.5 py-1 text-xs font-bold ${SCORE_STYLE[item.score_band]}`}>{item.score_band}</span>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        {item.is_demo_product ? <span className="rounded-md bg-amber-100 px-2.5 py-1 text-xs font-bold text-amber-950">{item.demo_label || "Demonstration Product"}</span> : null}
        {item.eligibility_status === "eligible_with_caution" ? <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-700">Eligible with caution</span> : null}
        <span className={`rounded-md px-2.5 py-1 text-xs font-bold ${CONFIDENCE_STYLE[item.recommendation_confidence]}`}>{displayCode(item.recommendation_confidence)} confidence</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 border-y border-slate-100 py-3 text-sm">
        <p><span className="text-slate-500">Price:</span> <strong>{formatPrice(item.price)}</strong></p>
        <p><span className="text-slate-500">Availability:</span> <strong>{displayCode(item.availability_status)}</strong></p>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-700">{item.why_recommended}</p>
      <section className="mt-4" aria-label="Positive recommendation factors">
        <h4 className="text-sm font-semibold text-slate-950">Why it matches</h4>
        <ul className="mt-2 space-y-2">
          {item.positive_factors.map((factor) => <li key={factor} className="flex items-start gap-2 text-sm leading-5 text-slate-700"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-leaf-700" aria-hidden="true" />{factor}</li>)}
        </ul>
      </section>
      {item.caution_factors.length ? (
        <section className="mt-4" aria-label="Recommendation cautions">
          <h4 className="text-sm font-semibold text-amber-950">Cautions to review</h4>
          <ul className="mt-2 space-y-2">
            {item.caution_factors.map((factor) => <li key={factor} className="flex items-start gap-2 text-sm leading-5 text-slate-700"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" aria-hidden="true" />{factor}</li>)}
          </ul>
        </section>
      ) : null}
      <ScoreBreakdown recommendation={item} />
      <button type="button" onClick={() => onView(item.product_id)} disabled={disabled} className="mt-5 inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-brand-600 px-4 py-2 text-sm font-semibold text-brand-700 hover:bg-brand-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 disabled:border-slate-300 disabled:text-slate-400">
        <Eye className="h-4 w-4" aria-hidden="true" />View Product Details
      </button>
    </article>
  );
}

function RecommendationDetailDialog({ detail, onClose }) {
  if (!detail) return null;
  const { product, recommendation } = detail;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/50 sm:items-center sm:p-6" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-t-lg bg-white p-6 shadow-xl sm:rounded-lg" role="dialog" aria-modal="true" aria-labelledby="recommendation-detail-title">
        <div className="flex items-start justify-between gap-4">
          <div><p className="text-xs font-semibold uppercase text-brand-700">Rank {recommendation.rank} {displayCode(product.category)}</p><h2 id="recommendation-detail-title" className="mt-1 text-2xl font-bold text-slate-950">{product.product_name}</h2><p className="mt-1 text-sm text-slate-600">{product.brand_name}</p></div>
          <button type="button" onClick={onClose} title="Close product details" aria-label="Close product details" className="rounded-md p-2 text-slate-600 hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-600"><X className="h-5 w-5" aria-hidden="true" /></button>
        </div>
        <p className="mt-5 text-sm leading-6 text-slate-700">{product.short_description}</p>
        <div className="mt-5 flex flex-wrap gap-2"><span className={`rounded-md px-2.5 py-1 text-xs font-bold ${SCORE_STYLE[recommendation.score_band]}`}>{recommendation.final_score}/100 {recommendation.score_band}</span>{product.is_demo_product ? <span className="rounded-md bg-amber-100 px-2.5 py-1 text-xs font-bold text-amber-950">Demonstration Product</span> : null}</div>
        <ScoreBreakdown recommendation={recommendation} />
        <p className="mt-6 border-t border-slate-200 pt-5 text-xs leading-5 text-slate-500">{detail.disclaimer}</p>
      </section>
    </div>
  );
}

export default function ProductRecommendationsPage() {
  const startedRef = useRef(false);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const {
    recommendationReport,
    selectedRecommendation,
    isGenerating,
    isLoadingProduct,
    generationProgress,
    error,
    generateCurrentRecommendations,
    loadRecommendationDetail,
    closeRecommendationDetail,
  } = useProductRecommendation();

  useEffect(() => {
    if (recommendationReport || isGenerating || error || startedRef.current) return;
    startedRef.current = true;
    generateCurrentRecommendations().catch(() => {});
  }, [recommendationReport, isGenerating, error, generateCurrentRecommendations]);

  const categories = useMemo(() => {
    if (!recommendationReport) return [];
    return Object.entries(recommendationReport.categories).filter(([, items]) => items.length);
  }, [recommendationReport]);

  if (isGenerating && !recommendationReport) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader eyebrow="Personalized catalogue relevance" title="Preparing Recommended Product Options" description="Only products that passed eligibility filtering can enter this deterministic ranking stage." />
        <GenerationProgress progress={generationProgress} />
      </section>
    );
  }

  if (!recommendationReport) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader eyebrow="Recommendations unavailable" title="Product Options Could Not Be Ranked Safely" description="No exclusions were weakened and no medical conclusion was generated." />
        <div className="mx-auto max-w-3xl border-y border-slate-200 py-8 text-center"><ErrorMessage id="recommendation-error" message={error} /><PrimaryButton className="mt-6" type="button" icon={RefreshCcw} onClick={() => generateCurrentRecommendations().catch(() => {})} disabled={isGenerating}>Try Again</PrimaryButton></div>
      </section>
    );
  }

  if (!recommendationReport.recommended_count) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader eyebrow="No qualifying catalogue options" title="No Sufficiently Relevant Products Were Found" description="The configured relevance threshold and all Step 11 safety exclusions were preserved." />
        <div className="mx-auto max-w-4xl space-y-7">
          <div className="flex items-start gap-4 border-y border-amber-200 bg-amber-50 px-4 py-7"><CircleHelp className="mt-0.5 h-6 w-6 shrink-0 text-amber-700" aria-hidden="true" /><div><h2 className="font-semibold text-slate-950">No safety threshold was lowered</h2><p className="mt-2 text-sm leading-6 text-slate-700">Review your non-allergy preferences, budget range, or catalogue coverage. Do not remove known allergy constraints merely to create a result.</p></div></div>
          <div className="grid gap-3 sm:grid-cols-3"><SecondaryButton to={ROUTES.skinProfile}>Review Skin Profile</SecondaryButton><SecondaryButton to={ROUTES.productEligibility}>Review Eligibility</SecondaryButton><SecondaryButton to={ROUTES.productDiscovery}>Browse Catalogue</SecondaryButton></div>
          <DisclaimerBox title="No recommendation is safer than an unsupported recommendation" />
        </div>
      </section>
    );
  }

  const visibleCategories = selectedCategory === "all"
    ? categories
    : categories.filter(([category]) => category === selectedCategory);
  return (
    <section className="px-4 py-14 sm:px-6 lg:px-8">
      <PageHeader eyebrow="Project-specific relevance ranking" title="Recommended Product Options" description="Compare category-ranked catalogue matches with their evidence, cautions, confidence, and score components." />
      <div className="mx-auto max-w-7xl space-y-9">
        <section className="flex flex-col gap-5 border-y border-brand-200 bg-brand-50 px-4 py-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-3"><ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-brand-700" aria-hidden="true" /><div><h2 className="font-semibold text-slate-950">Recommendation confidence: {displayCode(recommendationReport.overall_confidence)}</h2><ul className="mt-2 space-y-1 text-sm leading-6 text-slate-700">{recommendationReport.confidence_reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul></div></div>
          <dl className="grid shrink-0 grid-cols-2 gap-5 text-center"><div><dt className="text-xs uppercase text-slate-500">Eligible candidates</dt><dd className="mt-1 text-2xl font-bold text-slate-950">{recommendationReport.candidate_count}</dd></div><div><dt className="text-xs uppercase text-slate-500">Displayed options</dt><dd className="mt-1 text-2xl font-bold text-slate-950">{recommendationReport.recommended_count}</dd></div></dl>
        </section>

        <nav className="flex gap-2 overflow-x-auto border-b border-slate-200 pb-3" aria-label="Recommendation categories">
          <button type="button" onClick={() => setSelectedCategory("all")} className={`shrink-0 rounded-md px-4 py-2 text-sm font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-600 ${selectedCategory === "all" ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}`}>All Categories</button>
          {categories.map(([category, items]) => <button key={category} type="button" onClick={() => setSelectedCategory(category)} className={`shrink-0 rounded-md px-4 py-2 text-sm font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-600 ${selectedCategory === category ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}`}>{displayCode(category)} ({items.length})</button>)}
        </nav>

        <ErrorMessage id="recommendation-report-error" message={error} />
        <div className="space-y-12">
          {visibleCategories.map(([category, items]) => (
            <section key={category} aria-labelledby={`${category}-recommendations`}>
              <div className="flex items-center gap-3 border-b border-slate-200 pb-3"><Layers3 className="h-5 w-5 text-brand-700" aria-hidden="true" /><div><h2 id={`${category}-recommendations`} className="text-xl font-bold text-slate-950">Recommended {displayCode(category)} Options</h2><p className="mt-1 text-sm text-slate-600">Ranked within this category after eligibility, minimum-score, and diversity checks.</p></div></div>
              <div className="mt-5 grid gap-5 lg:grid-cols-2">{items.map((item) => <RecommendationCard key={item.product_id} item={item} onView={(productId) => loadRecommendationDetail(productId).catch(() => {})} disabled={isLoadingProduct} />)}</div>
            </section>
          ))}
        </div>

        <aside className="flex items-start gap-3 rounded-lg border border-clinic-200 bg-clinic-50 p-5"><Info className="mt-0.5 h-5 w-5 shrink-0 text-clinic-700" aria-hidden="true" /><div><h2 className="font-semibold text-slate-950">Report limitations</h2><ul className="mt-2 space-y-1 text-sm leading-6 text-slate-700">{recommendationReport.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul></div></aside>
        <DisclaimerBox title="Higher scores do not guarantee better results" description="Recommendation scores indicate how closely catalogue products match the available profile and visible skincare observations. Review the current label and manufacturer instructions, introduce new products cautiously, and seek qualified advice for severe or persistent concerns." />
        <div className="flex flex-col gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:flex-wrap sm:justify-between"><SecondaryButton to={ROUTES.productEligibility} icon={ArrowLeft}>Review Eligibility</SecondaryButton><SecondaryButton to={ROUTES.feedback} state={{ recommendationReportId: recommendationReport.recommendation_report_id, feedbackCategory: "product_recommendation_feedback", products: Object.values(recommendationReport.categories).flat() }} icon={MessageSquareText}>Recommendation Feedback</SecondaryButton><PrimaryButton to={ROUTES.skincareRoutine}>Build Skincare Routine</PrimaryButton></div>
      </div>
      <RecommendationDetailDialog detail={selectedRecommendation} onClose={closeRecommendationDetail} />
    </section>
  );
}
