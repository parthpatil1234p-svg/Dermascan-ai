import { Ban, Edit3, MessageSquareText, ShieldOff } from "lucide-react";
import { useEffect, useState } from "react";
import EmptyState from "../components/EmptyState";
import ErrorMessage from "../components/ErrorMessage";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import { ROUTES } from "../constants/appContent";
import { getFeedback, getFeedbackErrorMessage, getProductAvoidances, removeProductAvoidance, withdrawFeedback } from "../services/feedbackService";


function humanize(value) {
  return value?.toLowerCase().replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) || "Not provided";
}


export default function FeedbackHistoryPage() {
  const [items, setItems] = useState([]);
  const [avoidances, setAvoidances] = useState([]);
  const [confirming, setConfirming] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const load = async () => {
    setIsLoading(true); setError("");
    try {
      const [history, avoidanceData] = await Promise.all([
        getFeedback({ page: 1, page_size: 100 }), getProductAvoidances(),
      ]);
      setItems(history.feedback); setAvoidances(avoidanceData.avoidances);
    } catch (requestError) { setError(getFeedbackErrorMessage(requestError)); }
    finally { setIsLoading(false); }
  };
  useEffect(() => { load(); }, []);
  const withdraw = async (feedbackId) => {
    try { await withdrawFeedback(feedbackId); setConfirming(""); await load(); }
    catch (requestError) { setError(getFeedbackErrorMessage(requestError)); }
  };
  const removeAvoidance = async (productId) => {
    try { await removeProductAvoidance(productId); await load(); }
    catch (requestError) { setError(getFeedbackErrorMessage(requestError)); }
  };
  return (
    <section className="px-4 py-14 sm:px-6 lg:px-8">
      <PageHeader eyebrow="Owner-protected records" title="Feedback History" description="Review, edit, or withdraw your private submissions and manage product-avoidance preferences." />
      <div className="mx-auto max-w-6xl space-y-9"><ErrorMessage message={error} />
        {avoidances.length ? <section className="rounded-lg border border-amber-200 bg-amber-50 p-5"><div className="flex items-center gap-3"><ShieldOff className="h-5 w-5 text-amber-800" aria-hidden="true" /><h2 className="text-lg font-bold text-slate-950">Private product avoidance</h2></div><p className="mt-2 text-sm text-slate-700">These products are excluded only from your future eligibility results. Entries are user-reported preferences, not verified allergies.</p><div className="mt-4 space-y-3">{avoidances.map((item) => <div key={item.product_id} className="flex flex-col gap-3 rounded-md bg-white p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold text-slate-950">{item.product_name || item.product_id}</p><p className="mt-1 text-xs text-slate-500">Source: {item.source_feedback_id}</p></div><SecondaryButton type="button" icon={Ban} onClick={() => removeAvoidance(item.product_id)}>Remove Avoidance</SecondaryButton></div>)}</div></section> : null}
        <section aria-labelledby="feedback-records-heading"><div className="flex items-center justify-between gap-4"><h2 id="feedback-records-heading" className="text-xl font-bold text-slate-950">Your submissions</h2><PrimaryButton to={ROUTES.feedback}>New Feedback</PrimaryButton></div>
          {isLoading ? <p className="mt-6 text-sm font-semibold text-brand-700" role="status">Loading feedback history...</p> : null}
          {!isLoading && !items.length ? <div className="mt-6"><EmptyState icon={MessageSquareText} title="No feedback yet" description="Feedback is optional. You can share it after reviewing an analysis or final report." action={{ label: "Share Feedback", to: ROUTES.feedback }} /></div> : <div className="mt-5 grid gap-4 md:grid-cols-2">{items.map((item) => <article key={item.feedback_id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-bold text-brand-700">{item.feedback_id}</p><h3 className="mt-2 text-lg font-bold text-slate-950">{humanize(item.feedback_category)}</h3></div><span className={`rounded-md px-2 py-1 text-xs font-bold ${item.feedback_status === "withdrawn" ? "bg-slate-100 text-slate-600" : item.feedback_status === "flagged" ? "bg-amber-100 text-amber-900" : "bg-emerald-100 text-emerald-800"}`}>{humanize(item.feedback_status)}</span></div><dl className="mt-4 grid grid-cols-2 gap-3 text-sm"><div><dt className="text-slate-500">Report</dt><dd className="mt-1 font-medium text-slate-800">{item.final_report_id || item.recommendation_report_id || item.routine_report_id || "General"}</dd></div><div><dt className="text-slate-500">Rating</dt><dd className="mt-1 font-medium text-slate-800">{item.overall_rating || item.report_clarity || item.recommendation_relevance || item.routine_practicality || "Not rated"}</dd></div><div><dt className="text-slate-500">Submitted</dt><dd className="mt-1 text-slate-700">{new Date(item.created_at).toLocaleDateString("en-IN")}</dd></div><div><dt className="text-slate-500">Updated</dt><dd className="mt-1 text-slate-700">{new Date(item.updated_at).toLocaleDateString("en-IN")}</dd></div></dl>{item.product_name ? <p className="mt-3 text-sm text-slate-700">Product: {item.product_name}</p> : null}{item.feedback_status !== "withdrawn" ? <div className="mt-5 flex flex-wrap gap-2"><SecondaryButton to={`/feedback/${item.feedback_id}`} icon={Edit3}>Edit</SecondaryButton>{confirming === item.feedback_id ? <><span className="self-center text-sm font-semibold text-red-800">Withdraw this feedback?</span><SecondaryButton type="button" onClick={() => withdraw(item.feedback_id)}>Confirm</SecondaryButton><SecondaryButton type="button" onClick={() => setConfirming("")}>Cancel</SecondaryButton></> : <SecondaryButton type="button" icon={Ban} onClick={() => setConfirming(item.feedback_id)}>Withdraw</SecondaryButton>}</div> : null}</article>)}</div>}
        </section>
      </div>
    </section>
  );
}
