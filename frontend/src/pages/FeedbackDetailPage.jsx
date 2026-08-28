import { CheckCircle2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import FeedbackForm from "../components/FeedbackForm";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import { ROUTES } from "../constants/appContent";
import { getFeedbackById, getFeedbackErrorMessage, getFeedbackOptions, updateFeedback } from "../services/feedbackService";
import { getFinalReport } from "../services/finalReportService";
import { getProductRecommendationReport } from "../services/productRecommendationService";


export default function FeedbackDetailPage() {
  const { feedbackId } = useParams();
  const [feedback, setFeedback] = useState(null);
  const [options, setOptions] = useState(null);
  const [related, setRelated] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [item, optionData] = await Promise.all([getFeedbackById(feedbackId), getFeedbackOptions()]);
        if (!active) return;
        setFeedback(item); setOptions(optionData);
        if (item.final_report_id) setRelated(await getFinalReport(item.final_report_id));
        else if (item.upload_id && item.recommendation_report_id) setRelated(await getProductRecommendationReport(item.upload_id));
      } catch (requestError) { if (active) setError(getFeedbackErrorMessage(requestError)); }
      finally { if (active) setIsLoading(false); }
    }
    load(); return () => { active = false; };
  }, [feedbackId]);
  const save = async (payload) => {
    setIsSubmitting(true); setError("");
    try { setFeedback(await updateFeedback(feedbackId, payload)); setIsSaved(true); }
    catch (requestError) { setError(getFeedbackErrorMessage(requestError)); }
    finally { setIsSubmitting(false); }
  };
  if (isLoading) return <section className="px-4 py-16" role="status"><div className="mx-auto flex max-w-xl items-center justify-center gap-3 rounded-lg border border-slate-200 bg-white p-6 text-sm font-semibold text-slate-700 shadow-sm"><span className="h-6 w-6 animate-spin rounded-full border-2 border-brand-100 border-t-brand-600" aria-hidden="true" />Loading your feedback...</div></section>;
  if (!feedback || !options) return <section className="px-4 py-16 text-center"><p className="text-red-800">{error || "Feedback could not be loaded."}</p><PrimaryButton className="mt-5" to={ROUTES.feedbackHistory}>Feedback History</PrimaryButton></section>;
  const products = related?.product_recommendations || Object.values(related?.categories || {}).flat();
  const concerns = Object.values(related?.visible_concern_summary || {}).flat();
  return <section className="px-4 py-14 sm:px-6 lg:px-8"><PageHeader eyebrow={feedback.feedback_id} title="Edit Feedback" description="Update your structured response without changing its related historical report." /><div className="mx-auto max-w-6xl">{isSaved ? <div className="mb-6 flex items-center gap-3 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold text-emerald-900" role="status"><CheckCircle2 className="h-5 w-5" aria-hidden="true" />Your feedback changes were saved.</div> : null}<FeedbackForm key={feedback.updated_at} options={options} products={products} concerns={concerns} initialValues={feedback} lockedRelationship isSubmitting={isSubmitting} serverError={error} submitLabel="Update Feedback" onSubmit={save} /></div></section>;
}
