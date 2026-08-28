import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Eye,
  Filter,
  Info,
  RefreshCcw,
  ShieldAlert,
  ShieldCheck,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import DisclaimerBox from "../components/DisclaimerBox";
import ErrorMessage from "../components/ErrorMessage";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import {
  PRODUCT_ELIGIBILITY_STAGES,
  ROUTES,
} from "../constants/appContent";
import { PRODUCT_CATEGORIES, displayCode } from "../constants/catalogueOptions";
import { useProductEligibility } from "../context/ProductEligibilityContext";

const STATUS_DETAILS = {
  eligible: {
    label: "Eligible",
    description: "No exclusion or caution was found from the available data.",
    icon: CheckCircle2,
    badge: "bg-leaf-100 text-leaf-900",
    border: "border-leaf-200",
  },
  eligible_with_caution: {
    label: "Eligible with Caution",
    description: "No hard conflict was found, but one or more cautions need review.",
    icon: AlertTriangle,
    badge: "bg-amber-100 text-amber-950",
    border: "border-amber-200",
  },
  excluded: {
    label: "Excluded",
    description: "A strict safety, budget, age, or availability rule excluded this product.",
    icon: ShieldAlert,
    badge: "bg-red-100 text-red-900",
    border: "border-red-200",
  },
  insufficient_information: {
    label: "Insufficient Information",
    description: "The catalogue record is incomplete, so eligibility cannot be established safely.",
    icon: CircleHelp,
    badge: "bg-slate-200 text-slate-800",
    border: "border-slate-300",
  },
};

const STATUS_OPTIONS = [
  ["", "All eligibility statuses"],
  ["eligible", "Eligible"],
  ["eligible_with_caution", "Eligible with caution"],
  ["insufficient_information", "Insufficient information"],
  ["excluded", "Excluded"],
];

const STATUS_ORDER = [
  "eligible",
  "eligible_with_caution",
  "insufficient_information",
  "excluded",
];

function formatPrice(price) {
  if (!price) return "Price unavailable";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: price.currency,
    maximumFractionDigits: 2,
  }).format(price.amount);
}

function EvaluationProgress({ progress }) {
  const activeIndex = Math.min(
    PRODUCT_ELIGIBILITY_STAGES.length - 1,
    Math.floor((progress / 100) * PRODUCT_ELIGIBILITY_STAGES.length),
  );
  return (
    <div className="mx-auto max-w-3xl border-y border-slate-200 py-8" role="status">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-950">Checking catalogue eligibility</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Applying strict exclusions, cautions, compatibility checks, and data-quality rules.
          </p>
        </div>
        <span className="text-lg font-bold text-brand-700">{progress}%</span>
      </div>
      <div
        className="mt-5 h-2 overflow-hidden rounded-full bg-slate-200"
        role="progressbar"
        aria-label="Product eligibility evaluation progress"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow={progress}
      >
        <div className="h-full rounded-full bg-brand-600 transition-all" style={{ width: `${progress}%` }} />
      </div>
      <ol className="mt-6 grid gap-3 sm:grid-cols-2">
        {PRODUCT_ELIGIBILITY_STAGES.map((stage, index) => (
          <li key={stage} className={`flex items-center gap-3 text-sm ${index <= activeIndex ? "font-semibold text-slate-900" : "text-slate-500"}`}>
            <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${index < activeIndex ? "bg-leaf-600" : index === activeIndex ? "animate-pulse bg-brand-600" : "bg-slate-300"}`} />
            {stage}
          </li>
        ))}
      </ol>
    </div>
  );
}

function StatusBadge({ status }) {
  const details = STATUS_DETAILS[status];
  const Icon = details.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-bold ${details.badge}`}>
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {details.label}
    </span>
  );
}

function SummaryItem({ label, value, tone }) {
  return (
    <div className={`border-l-4 px-4 py-2 ${tone}`}>
      <dt className="text-sm text-slate-600">{label}</dt>
      <dd className="mt-1 text-2xl font-bold text-slate-950">{value}</dd>
    </div>
  );
}

function ProductEligibilityCard({ candidate, onView, disabled }) {
  const details = STATUS_DETAILS[candidate.eligibility_status];
  return (
    <article className={`rounded-lg border bg-white p-5 shadow-sm ${details.border}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase text-slate-500">{displayCode(candidate.category)}</p>
          <h3 className="mt-1 text-lg font-semibold text-slate-950">{candidate.product_name}</h3>
          <p className="mt-1 text-sm text-slate-600">{candidate.brand_name}</p>
        </div>
        <StatusBadge status={candidate.eligibility_status} />
      </div>
      {candidate.is_demo_product ? (
        <p className="mt-4 inline-flex rounded-md bg-clinic-100 px-2.5 py-1 text-xs font-bold text-clinic-900">
          {candidate.demo_label || "Demonstration Product"}
        </p>
      ) : null}
      <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 border-y border-slate-100 py-3 text-sm">
        <p><span className="text-slate-500">Price:</span> <strong>{formatPrice(candidate.price)}</strong></p>
        <p><span className="text-slate-500">Availability:</span> <strong>{displayCode(candidate.availability_status)}</strong></p>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-700">{details.description}</p>
      {candidate.primary_reasons.length ? (
        <ul className="mt-3 space-y-2">
          {candidate.primary_reasons.map((reason) => (
            <li key={`${candidate.product_id}-${reason.code}`} className="flex items-start gap-2 text-sm leading-5 text-slate-700">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-brand-700" aria-hidden="true" />
              <span>{reason.message}</span>
            </li>
          ))}
        </ul>
      ) : null}
      <div className="mt-5 flex items-center justify-between gap-3">
        <p className="text-xs text-slate-500">
          {candidate.positive_match_count} matches, {candidate.caution_count} cautions, {candidate.information_gap_count} gaps
        </p>
        <button
          type="button"
          onClick={() => onView(candidate.product_id)}
          disabled={disabled}
          className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold text-brand-700 hover:bg-brand-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 disabled:text-slate-400"
        >
          <Eye className="h-4 w-4" aria-hidden="true" />
          View reasons
        </button>
      </div>
    </article>
  );
}

function ReasonList({ title, reasons, tone = "text-slate-700" }) {
  if (!reasons.length) return null;
  return (
    <section>
      <h3 className="font-semibold text-slate-950">{title}</h3>
      <ul className="mt-3 space-y-3">
        {reasons.map((reason) => (
          <li key={`${title}-${reason.code}`} className={`border-l-2 border-slate-200 pl-3 text-sm leading-6 ${tone}`}>
            <p>{reason.message}</p>
            <p className="mt-1 font-mono text-xs text-slate-500">{reason.code}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

function ProductDetailDialog({ detail, onClose }) {
  if (!detail) return null;
  const { product } = detail;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/50 p-0 sm:items-center sm:p-6" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-t-lg bg-white p-6 shadow-xl sm:rounded-lg" role="dialog" aria-modal="true" aria-labelledby="eligibility-detail-title">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase text-slate-500">{displayCode(product.category)}</p>
            <h2 id="eligibility-detail-title" className="mt-1 text-2xl font-bold text-slate-950">{product.product_name}</h2>
            <p className="mt-1 text-sm text-slate-600">{product.brand_name}</p>
          </div>
          <button type="button" onClick={onClose} title="Close product details" aria-label="Close product details" className="rounded-md p-2 text-slate-600 hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-600">
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
        <div className="mt-5"><StatusBadge status={detail.eligibility_status} /></div>
        <p className="mt-4 text-sm leading-6 text-slate-700">{product.short_description}</p>
        {product.is_demo_product ? <p className="mt-4 rounded-md bg-clinic-50 p-3 text-sm font-semibold text-clinic-900">Demonstration product data. Verify real product details before purchase.</p> : null}
        <div className="mt-6 grid gap-7 md:grid-cols-2">
          <ReasonList title="Hard exclusions" reasons={detail.hard_exclusions} tone="text-red-800" />
          <ReasonList title="Cautions" reasons={detail.cautions} tone="text-amber-900" />
          <ReasonList title="Positive matches" reasons={detail.positive_matches} tone="text-leaf-900" />
          <ReasonList title="Information gaps" reasons={detail.information_gaps} />
        </div>
        <p className="mt-7 border-t border-slate-200 pt-5 text-xs leading-5 text-slate-500">{detail.disclaimer}</p>
      </section>
    </div>
  );
}

export default function ProductEligibilityPage() {
  const startedRef = useRef(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const {
    eligibilityReport,
    selectedProduct,
    isEvaluating,
    isLoadingReport,
    isLoadingProduct,
    evaluationProgress,
    error,
    evaluateCurrentProducts,
    loadReport,
    loadProductDetail,
    closeProductDetail,
  } = useProductEligibility();

  useEffect(() => {
    if (eligibilityReport || isEvaluating || error || startedRef.current) return;
    startedRef.current = true;
    evaluateCurrentProducts().catch(() => {});
  }, [eligibilityReport, isEvaluating, error, evaluateCurrentProducts]);

  const applyFilters = async (nextStatus, nextCategory, page = 1) => {
    setStatusFilter(nextStatus);
    setCategoryFilter(nextCategory);
    try {
      await loadReport({
        ...(nextStatus ? { status: nextStatus } : {}),
        ...(nextCategory ? { category: nextCategory } : {}),
        page,
        page_size: 20,
      });
    } catch {
      // The context exposes the safe backend message.
    }
  };

  const retryEvaluation = () => {
    startedRef.current = true;
    evaluateCurrentProducts().catch(() => {});
  };

  if (isEvaluating && !eligibilityReport) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader eyebrow="Safety-first catalogue review" title="Evaluating Product Eligibility" description="Products are filtered using your saved profile and completed analysis reports. This is not a recommendation ranking." />
        <EvaluationProgress progress={evaluationProgress} />
      </section>
    );
  }

  if (!eligibilityReport) {
    return (
      <section className="px-4 py-14 sm:px-6 lg:px-8">
        <PageHeader eyebrow="Eligibility unavailable" title="The Catalogue Could Not Be Filtered Safely" description="No products were ranked or presented as suitable." />
        <div className="mx-auto max-w-3xl border-y border-slate-200 py-8 text-center">
          <ErrorMessage id="eligibility-error" message={error} />
          <PrimaryButton className="mt-6" type="button" icon={RefreshCcw} onClick={retryEvaluation} disabled={isEvaluating}>Try Again</PrimaryButton>
        </div>
      </section>
    );
  }

  const { summary, pagination } = eligibilityReport;
  const groupedCandidates = STATUS_ORDER.map((status) => ({
    status,
    items: eligibilityReport.candidate_products.filter(
      (candidate) => candidate.eligibility_status === status,
    ),
  })).filter((group) => group.items.length);
  return (
    <section className="px-4 py-14 sm:px-6 lg:px-8">
      <PageHeader eyebrow="Rule-based eligibility" title="Product Eligibility Report" description="Review which catalogue products passed strict profile checks, require caution, were excluded, or need better source data." />
      <div className="mx-auto max-w-7xl space-y-9">
        <div className="flex items-start gap-3 border-y border-brand-200 bg-brand-50 px-4 py-5 text-sm leading-6 text-slate-700">
          <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-brand-700" aria-hidden="true" />
          <p><strong>This is eligibility filtering, not ranking.</strong> A product remaining eligible does not guarantee safety, effectiveness, availability, or suitability. Product details and formulas can change.</p>
        </div>

        <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <SummaryItem label="Evaluated" value={summary.total_evaluated} tone="border-brand-500" />
          <SummaryItem label="Eligible" value={summary.eligible} tone="border-leaf-500" />
          <SummaryItem label="With caution" value={summary.eligible_with_caution} tone="border-amber-500" />
          <SummaryItem label="Information gaps" value={summary.insufficient_information} tone="border-slate-400" />
          <SummaryItem label="Excluded" value={summary.excluded} tone="border-red-500" />
        </dl>

        <section className="border-y border-slate-200 py-5" aria-labelledby="filter-heading">
          <div className="flex items-center gap-2"><Filter className="h-5 w-5 text-brand-700" aria-hidden="true" /><h2 id="filter-heading" className="text-lg font-semibold text-slate-950">Filter report</h2></div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:max-w-3xl">
            <label className="text-sm font-semibold text-slate-800">Eligibility status
              <select value={statusFilter} onChange={(event) => applyFilters(event.target.value, categoryFilter)} disabled={isLoadingReport} className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 font-normal focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200">
                {STATUS_OPTIONS.map(([value, label]) => <option key={value || "all"} value={value}>{label}</option>)}
              </select>
            </label>
            <label className="text-sm font-semibold text-slate-800">Product category
              <select value={categoryFilter} onChange={(event) => applyFilters(statusFilter, event.target.value)} disabled={isLoadingReport} className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 font-normal focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200">
                <option value="">All categories</option>
                {PRODUCT_CATEGORIES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            </label>
          </div>
        </section>

        <ErrorMessage id="eligibility-report-error" message={error} />
        {isLoadingReport ? <p className="text-sm font-semibold text-brand-700" role="status">Updating report view...</p> : null}
        {eligibilityReport.candidate_products.length ? (
          <div className="space-y-10">
            {groupedCandidates.map((group) => {
              const details = STATUS_DETAILS[group.status];
              return (
                <section key={group.status} aria-labelledby={`${group.status}-heading`}>
                  <div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-200 pb-3">
                    <div>
                      <h2 id={`${group.status}-heading`} className="text-xl font-bold text-slate-950">{details.label} Products</h2>
                      <p className="mt-1 text-sm text-slate-600">{details.description}</p>
                    </div>
                    <span className="text-sm font-semibold text-slate-600">{group.items.length} on this page</span>
                  </div>
                  <div className="mt-5 grid gap-5 lg:grid-cols-2">
                    {group.items.map((candidate) => (
                      <ProductEligibilityCard key={candidate.product_id} candidate={candidate} onView={(productId) => loadProductDetail(productId).catch(() => {})} disabled={isLoadingProduct} />
                    ))}
                  </div>
                </section>
              );
            })}
          </div>
        ) : (
          <div className="border-y border-slate-200 py-10 text-center">
            <CircleHelp className="mx-auto h-8 w-8 text-slate-400" aria-hidden="true" />
            <h2 className="mt-3 text-lg font-semibold text-slate-950">No products match these report filters</h2>
            <button type="button" onClick={() => applyFilters("", "")} className="mt-3 text-sm font-semibold text-brand-700 hover:text-brand-800">Clear filters</button>
          </div>
        )}

        {pagination.total_pages > 1 ? (
          <nav className="flex items-center justify-between border-t border-slate-200 pt-5" aria-label="Eligibility report pages">
            <button type="button" disabled={!pagination.has_previous || isLoadingReport} onClick={() => applyFilters(statusFilter, categoryFilter, pagination.page - 1)} className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 disabled:text-slate-400"><ChevronLeft className="h-4 w-4" aria-hidden="true" />Previous</button>
            <p className="text-sm text-slate-600">Page {pagination.page} of {pagination.total_pages}</p>
            <button type="button" disabled={!pagination.has_next || isLoadingReport} onClick={() => applyFilters(statusFilter, categoryFilter, pagination.page + 1)} className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 disabled:text-slate-400">Next<ChevronRight className="h-4 w-4" aria-hidden="true" /></button>
          </nav>
        ) : null}

        <DisclaimerBox title="Eligibility does not guarantee safety" description="Always verify the current ingredient list, price, availability, directions, and warnings on the product packaging or official source. Patch-test new products when appropriate and consult a qualified professional for allergy or medical concerns." />
        <div className="flex flex-col gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:justify-between">
          <SecondaryButton to={ROUTES.skinConcernAnalysis} icon={ArrowLeft}>Review Visible Observations</SecondaryButton>
          <div className="flex flex-col gap-3 sm:flex-row">
            <SecondaryButton to={ROUTES.productDiscovery} icon={Eye}>Browse Full Catalogue</SecondaryButton>
            <PrimaryButton to={ROUTES.productRecommendations} icon={ArrowRight}>View Recommended Options</PrimaryButton>
          </div>
        </div>
      </div>
      <ProductDetailDialog detail={selectedProduct} onClose={closeProductDetail} />
    </section>
  );
}
