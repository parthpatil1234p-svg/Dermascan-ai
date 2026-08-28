import { AlertTriangle, CheckCircle2, Info, ShieldCheck, Star } from "lucide-react";
import { useMemo, useState } from "react";
import ErrorMessage from "./ErrorMessage";
import PrimaryButton from "./PrimaryButton";
import SecondaryButton from "./SecondaryButton";


const CATEGORY_GROUPS = [
  { title: "Analysis Result", values: ["analysis_feedback", "skin_type_feedback", "skin_concern_feedback"] },
  { title: "Product Recommendations", values: ["product_recommendation_feedback", "product_experience_feedback"] },
  { title: "Skincare Routine", values: ["routine_feedback"] },
  { title: "Final Report", values: ["report_feedback"] },
  { title: "General Experience", values: ["application_feedback"] },
];

const EMPTY_FORM = {
  final_report_id: "",
  recommendation_report_id: "",
  routine_report_id: "",
  product_id: "",
  feedback_category: "analysis_feedback",
  overall_rating: "",
  helpfulness_rating: "",
  clarity_rating: "",
  accuracy_perception: "",
  concern_code: "",
  user_assessment: "",
  recommendation_relevance: "",
  price_feedback: "",
  availability_feedback: "",
  preference_match: null,
  product_experience_status: "",
  irritation_reported: "",
  irritation_description: "",
  exclude_product_from_future_recommendations: false,
  routine_practicality: "",
  routine_difficulty: "",
  step_count_preference: "",
  morning_routine_feedback: "",
  night_routine_feedback: "",
  report_clarity: "",
  report_length: "",
  technical_detail_level: "",
  export_experience: "",
  selected_reasons: [],
  comment: "",
  consent_for_analytics: false,
  consent_for_research_review: false,
  is_anonymous_for_aggregate_use: true,
};

const NUMBER_FIELDS = new Set([
  "overall_rating", "helpfulness_rating", "clarity_rating",
  "recommendation_relevance", "routine_practicality", "report_clarity",
]);

const PRODUCT_CATEGORIES = new Set([
  "product_recommendation_feedback", "product_experience_feedback",
]);

function humanize(value) {
  return value.toLowerCase().replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function RatingField({ label, name, value, options, onChange }) {
  return (
    <fieldset>
      <legend className="text-sm font-semibold text-slate-800">{label}</legend>
      <div className="mt-2 grid grid-cols-5 gap-2">
        {options.map((option) => (
          <label key={option.value} className={`flex min-w-0 cursor-pointer flex-col items-center gap-1 rounded-md border px-2 py-2 text-center text-xs font-semibold transition focus-within:outline focus-within:outline-2 focus-within:outline-brand-600 ${Number(value) === option.value ? "border-brand-600 bg-brand-50 text-brand-800" : "border-slate-200 bg-white text-slate-600 hover:border-brand-300"}`}>
            <input className="sr-only" type="radio" name={name} value={option.value} checked={Number(value) === option.value} onChange={onChange} />
            <Star className="h-4 w-4" fill={Number(value) >= option.value ? "currentColor" : "none"} aria-hidden="true" />
            <span>{option.value}</span>
            <span className="hidden leading-4 sm:block">{option.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function SelectField({ label, name, value, options, onChange, required = false, placeholder = "Select an option" }) {
  return (
    <label className="block text-sm font-semibold text-slate-800">
      {label}{required ? <span className="text-red-700"> *</span> : null}
      <select name={name} value={value ?? ""} onChange={onChange} required={required} className="mt-2 w-full rounded-md border border-slate-300 bg-white px-3 py-3 text-sm text-slate-900 focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100">
        <option value="">{placeholder}</option>
        {options.map((option) => {
          const item = typeof option === "string" ? { value: option, label: humanize(option) } : option;
          return <option key={item.value} value={item.value}>{item.label}</option>;
        })}
      </select>
    </label>
  );
}

function categoryReasons(options, category) {
  if (!options) return [];
  if (category === "product_experience_feedback") return options.reason_groups.product_experience;
  if (PRODUCT_CATEGORIES.has(category)) {
    return [...options.reason_groups.positive, ...options.reason_groups.negative, ...options.reason_groups.product_experience];
  }
  return [...options.reason_groups.positive, ...options.reason_groups.negative];
}

function buildPayload(form) {
  return Object.fromEntries(Object.keys(EMPTY_FORM).map((key) => {
    const value = form[key];
    if (NUMBER_FIELDS.has(key)) return [key, value == null || value === "" ? null : Number(value)];
    if (value === "") return [key, null];
    return [key, value];
  }));
}

function validate(form) {
  const related = form.final_report_id || form.recommendation_report_id || form.routine_report_id;
  if (form.feedback_category !== "application_feedback" && !related) return "Select the report this feedback relates to.";
  if (PRODUCT_CATEGORIES.has(form.feedback_category) && !form.product_id) return "Select a recommended product.";
  if (form.feedback_category === "skin_type_feedback" && !form.accuracy_perception) return "Select how the skin-type estimate compares with your experience.";
  if (form.feedback_category === "skin_concern_feedback" && (!form.concern_code || !form.user_assessment)) return "Select a visible observation and assessment.";
  if (form.feedback_category === "product_experience_feedback" && (!form.product_experience_status || !form.irritation_reported)) return "Confirm your product-use experience and response.";
  if (form.feedback_category === "routine_feedback" && !form.routine_practicality && !form.routine_difficulty) return "Rate the routine practicality or select its difficulty.";
  if (form.feedback_category === "report_feedback" && !form.report_clarity && !form.overall_rating) return "Rate the report clarity or overall experience.";
  if (["analysis_feedback", "application_feedback"].includes(form.feedback_category) && !form.overall_rating && !form.comment.trim()) return "Provide an overall rating or comment.";
  if (form.comment.length > 1000) return "Feedback comments must not exceed 1000 characters.";
  return "";
}

export default function FeedbackForm({
  options,
  reports = [],
  products = [],
  concerns = [],
  initialValues,
  lockedRelationship = false,
  isSubmitting,
  serverError,
  submitLabel = "Submit Feedback",
  onReportChange,
  onSubmit,
}) {
  const [form, setForm] = useState(() => ({ ...EMPTY_FORM, ...initialValues }));
  const [validationError, setValidationError] = useState("");
  const reasons = useMemo(() => categoryReasons(options, form.feedback_category), [options, form.feedback_category]);
  if (!options) return null;

  const update = (event) => {
    const { name, type, checked, value } = event.target;
    setValidationError("");
    setForm((current) => ({ ...current, [name]: type === "checkbox" ? checked : value }));
  };
  const changeReport = (event) => {
    setValidationError("");
    setForm((current) => ({
      ...current,
      final_report_id: event.target.value,
      product_id: "",
      concern_code: "",
    }));
    onReportChange?.(event.target.value);
  };
  const toggleReason = (reason) => {
    setForm((current) => ({
      ...current,
      selected_reasons: current.selected_reasons.includes(reason)
        ? current.selected_reasons.filter((item) => item !== reason)
        : [...current.selected_reasons, reason],
    }));
  };
  const submit = async (event) => {
    event.preventDefault();
    const message = validate(form);
    if (message) { setValidationError(message); return; }
    await onSubmit(buildPayload(form));
  };
  const values = options.values;
  const showsIrritationWarning = ["mild_discomfort", "visible_irritation", "serious_reaction"].includes(form.irritation_reported);

  return (
    <form onSubmit={submit} className="space-y-8" noValidate>
      <section className="border-y border-slate-200 py-6" aria-labelledby="feedback-category-heading">
        <h2 id="feedback-category-heading" className="text-xl font-bold text-slate-950">What would you like to review?</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {CATEGORY_GROUPS.map((group) => (
            <div key={group.title}>
              <p className="mb-2 text-xs font-bold uppercase text-slate-500">{group.title}</p>
              <div className="space-y-2">{group.values.map((value) => {
                const item = options.categories.find((category) => category.value === value);
                return <label key={value} className={`flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm font-semibold ${form.feedback_category === value ? "border-brand-600 bg-brand-50 text-brand-800" : "border-slate-200 text-slate-700"}`}><input type="radio" name="feedback_category" value={value} checked={form.feedback_category === value} onChange={update} />{item?.label || humanize(value)}</label>;
              })}</div>
            </div>
          ))}
        </div>
      </section>

      {form.feedback_category !== "application_feedback" ? (
        <section className="grid gap-5 rounded-lg border border-slate-200 bg-white p-5 md:grid-cols-2" aria-labelledby="feedback-context-heading">
          <div><h2 id="feedback-context-heading" className="text-lg font-bold text-slate-950">Related analysis</h2><p className="mt-1 text-sm leading-6 text-slate-600">Feedback is linked to an owned historical snapshot. It will not rewrite that report.</p></div>
          {lockedRelationship ? <div className="rounded-md bg-slate-50 p-4 text-sm font-semibold text-slate-700">{form.final_report_id || form.recommendation_report_id || form.routine_report_id}</div> : <SelectField label="Final report" name="final_report_id" value={form.final_report_id} options={reports.map((report) => ({ value: report.final_report_id, label: `${report.final_report_id} - ${report.skin_type}` }))} onChange={changeReport} required />}
        </section>
      ) : null}

      <section className="grid gap-6 rounded-lg border border-slate-200 bg-white p-5 md:grid-cols-2" aria-labelledby="feedback-details-heading">
        <h2 id="feedback-details-heading" className="md:col-span-2 text-xl font-bold text-slate-950">Structured feedback</h2>
        {["analysis_feedback", "application_feedback"].includes(form.feedback_category) ? <RatingField label="Overall experience" name="overall_rating" value={form.overall_rating} options={options.ratings} onChange={update} /> : null}
        {form.feedback_category === "skin_type_feedback" ? <SelectField label="Does the estimate match your normal experience?" name="accuracy_perception" value={form.accuracy_perception} options={values.accuracy_perception} onChange={update} required /> : null}
        {form.feedback_category === "skin_concern_feedback" ? <><SelectField label="Visible observation" name="concern_code" value={form.concern_code} options={concerns.map((item) => ({ value: item.code, label: item.name }))} onChange={update} required /><SelectField label="Was this observation useful?" name="user_assessment" value={form.user_assessment} options={values.user_assessment} onChange={update} required /></> : null}
        {PRODUCT_CATEGORIES.has(form.feedback_category) ? <><SelectField label="Recommended product" name="product_id" value={form.product_id} options={products.map((item) => ({ value: item.product_id, label: `${item.product_name} - ${item.brand_name}` }))} onChange={update} required /><RatingField label="Recommendation relevance" name="recommendation_relevance" value={form.recommendation_relevance} options={options.ratings} onChange={update} /><SelectField label="Price" name="price_feedback" value={form.price_feedback} options={values.price_feedback} onChange={update} /><SelectField label="Availability" name="availability_feedback" value={form.availability_feedback} options={values.availability_feedback} onChange={update} /></> : null}
        {form.feedback_category === "product_experience_feedback" ? <><SelectField label="I have used this product" name="product_experience_status" value={form.product_experience_status} options={values.product_experience_status} onChange={update} required /><SelectField label="Response after use" name="irritation_reported" value={form.irritation_reported} options={values.irritation_reported} onChange={update} required />{showsIrritationWarning ? <div className="md:col-span-2 rounded-lg border border-amber-300 bg-amber-50 p-4"><div className="flex gap-3"><AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-800" aria-hidden="true" /><div><p className="font-semibold text-amber-950">You reported a negative skin response.</p><p className="mt-1 text-sm leading-6 text-amber-900">DermaScan AI cannot diagnose the cause. Stop using the product if discomfort continues, review the current label, and seek appropriate professional guidance for severe or persistent reactions.</p><label className="mt-3 flex items-start gap-2 text-sm font-semibold text-amber-950"><input type="checkbox" name="exclude_product_from_future_recommendations" checked={form.exclude_product_from_future_recommendations} onChange={update} className="mt-1" />Exclude this product from my future recommendations</label></div></div></div> : null}</> : null}
        {form.feedback_category === "routine_feedback" ? <><RatingField label="Routine practicality" name="routine_practicality" value={form.routine_practicality} options={options.ratings} onChange={update} /><SelectField label="Routine difficulty" name="routine_difficulty" value={form.routine_difficulty} options={values.routine_difficulty} onChange={update} /></> : null}
        {form.feedback_category === "report_feedback" ? <><RatingField label="Report clarity" name="report_clarity" value={form.report_clarity} options={options.ratings} onChange={update} /><SelectField label="Report length" name="report_length" value={form.report_length} options={values.report_length} onChange={update} /><SelectField label="Technical detail" name="technical_detail_level" value={form.technical_detail_level} options={values.technical_detail_level} onChange={update} /></> : null}
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5" aria-labelledby="feedback-reasons-heading">
        <h2 id="feedback-reasons-heading" className="text-xl font-bold text-slate-950">Reasons and comments</h2>
        <p className="mt-1 text-sm text-slate-600">Choose stable reasons where they apply. Comments remain private and are not public reviews.</p>
        <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{reasons.map((reason) => <label key={reason} className="flex items-start gap-2 rounded-md border border-slate-200 p-3 text-sm text-slate-700"><input type="checkbox" checked={form.selected_reasons.includes(reason)} onChange={() => toggleReason(reason)} className="mt-0.5" /><span>{humanize(reason)}</span></label>)}</div>
        <label className="mt-5 block text-sm font-semibold text-slate-800">Additional comments<textarea name="comment" value={form.comment} onChange={update} maxLength={1000} rows={5} className="mt-2 w-full rounded-md border border-slate-300 px-3 py-3 text-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" /><span className="mt-1 block text-right text-xs font-normal text-slate-500">{form.comment.length}/1000</span></label>
      </section>

      <section className="rounded-lg border border-clinic-200 bg-clinic-50 p-5" aria-labelledby="feedback-consent-heading">
        <div className="flex gap-3"><ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-clinic-800" aria-hidden="true" /><div className="w-full"><h2 id="feedback-consent-heading" className="font-bold text-slate-950">Optional feedback consent</h2><p className="mt-1 text-sm leading-6 text-slate-700">Feedback can be submitted without either consent. Facial-image processing consent does not apply here.</p><label className="mt-4 flex items-start gap-2 text-sm text-slate-800"><input type="checkbox" name="consent_for_analytics" checked={form.consent_for_analytics} onChange={update} className="mt-1" />Allow de-identified aggregate product and workflow analytics.</label><label className="mt-3 flex items-start gap-2 text-sm text-slate-800"><input type="checkbox" name="consent_for_research_review" checked={form.consent_for_research_review} onChange={update} className="mt-1" />Allow authorized project-team review for academic evaluation.</label></div></div>
      </section>

      <div className="flex items-start gap-3 border-y border-slate-200 py-5 text-sm leading-6 text-slate-700"><Info className="mt-0.5 h-5 w-5 shrink-0 text-brand-700" aria-hidden="true" /><p>Feedback is stored separately from your facial image. It is self-reported information, is not medical evidence, and is not automatically used to retrain the AI model.</p></div>
      <ErrorMessage id="feedback-form-error" message={validationError || serverError} />
      <div className="flex flex-col gap-3 sm:flex-row sm:justify-end"><SecondaryButton to="/feedback/history">Feedback History</SecondaryButton><PrimaryButton type="submit" disabled={isSubmitting} icon={isSubmitting ? undefined : CheckCircle2}>{isSubmitting ? "Saving Feedback..." : submitLabel}</PrimaryButton></div>
    </form>
  );
}

export { EMPTY_FORM };
