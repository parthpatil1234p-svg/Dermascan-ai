import { CheckCircle2, History, MessageSquareText } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import FeedbackForm from "../components/FeedbackForm";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import { ROUTES } from "../constants/appContent";
import { getFeedbackErrorMessage, getFeedbackOptions, submitFeedback } from "../services/feedbackService";
import { getFinalReport, getUserReports } from "../services/finalReportService";


function observations(report) {
  if (!report) return [];
  return Object.values(report.visible_concern_summary || {}).flat();
}


export default function FeedbackPage() {
  const { state } = useLocation();
  const [options, setOptions] = useState(null);
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(state?.report || null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [savedFeedback, setSavedFeedback] = useState(null);

  const lockedRelationship = Boolean(
    state?.finalReportId || state?.recommendationReportId || state?.routineReportId,
  );
  const initialValues = useMemo(() => ({
    feedback_category: state?.feedbackCategory || "analysis_feedback",
    final_report_id: state?.finalReportId || "",
    recommendation_report_id: state?.recommendationReportId || "",
    routine_report_id: state?.routineReportId || "",
    product_id: state?.productId || "",
  }), [state]);
  const products = selectedReport?.product_recommendations || state?.products || [];
  const concerns = observations(selectedReport).length ? observations(selectedReport) : state?.concerns || [];

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [feedbackOptions, history] = await Promise.all([
          getFeedbackOptions(), getUserReports({ page: 1, page_size: 100, sort: "newest" }),
        ]);
        if (!active) return;
        setOptions(feedbackOptions);
        setReports(history.reports);
        if (state?.finalReportId && !state?.report) {
          const report = await getFinalReport(state.finalReportId);
          if (active) setSelectedReport(report);
        }
      } catch (requestError) {
        if (active) setError(getFeedbackErrorMessage(requestError));
      } finally {
        if (active) setIsLoading(false);
      }
    }
    load();
    return () => { active = false; };
  }, [state?.finalReportId, state?.report]);

  const handleReportChange = async (reportId) => {
    setSelectedReport(null);
    if (!reportId) return;
    try {
      setSelectedReport(await getFinalReport(reportId));
    } catch (requestError) {
      setError(getFeedbackErrorMessage(requestError));
    }
  };
  const handleSubmit = async (payload) => {
    setIsSubmitting(true); setError("");
    try { setSavedFeedback(await submitFeedback(payload)); }
    catch (requestError) { setError(getFeedbackErrorMessage(requestError)); }
    finally { setIsSubmitting(false); }
  };

  if (isLoading) return <section className="px-4 py-16" role="status"><div className="mx-auto flex max-w-xl items-center justify-center gap-3 rounded-lg border border-slate-200 bg-white p-6 text-sm font-semibold text-slate-700 shadow-sm"><span className="h-6 w-6 animate-spin rounded-full border-2 border-brand-100 border-t-brand-600" aria-hidden="true" />Loading private feedback options...</div></section>;
  if (savedFeedback) return (
    <section className="px-4 py-16 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl rounded-lg border border-emerald-200 bg-white p-8 text-center shadow-sm">
        <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-700" aria-hidden="true" />
        <h1 className="mt-4 text-2xl font-bold text-slate-950">Feedback Saved</h1>
        <p className="mt-3 leading-7 text-slate-700">{savedFeedback.acknowledgement}</p>
        <p className="mt-3 text-sm text-slate-600">Reference: {savedFeedback.feedback_id}. This submission does not modify your historical report or automatically retrain an AI model.</p>
        <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row"><SecondaryButton to={ROUTES.reports}>Report History</SecondaryButton><PrimaryButton to={ROUTES.feedbackHistory} icon={History}>Feedback History</PrimaryButton></div>
      </div>
    </section>
  );
  return (
    <section className="px-4 py-14 sm:px-6 lg:px-8">
      <PageHeader eyebrow="Optional user-reported information" title="Share Structured Feedback" description="Review an analysis, recommendation, routine, report, or application experience without changing the original result." />
      <div className="mx-auto max-w-6xl">
        <div className="mb-7 flex items-start gap-3 border-y border-brand-200 bg-brand-50 px-4 py-5"><MessageSquareText className="mt-0.5 h-5 w-5 shrink-0 text-brand-700" aria-hidden="true" /><p className="text-sm leading-6 text-slate-700">Feedback is optional and self-reported. It does not validate medical conclusions, product safety, or AI model accuracy.</p></div>
        <FeedbackForm options={options} reports={reports} products={products} concerns={concerns} initialValues={initialValues} lockedRelationship={lockedRelationship} isSubmitting={isSubmitting} serverError={error} onReportChange={handleReportChange} onSubmit={handleSubmit} />
      </div>
    </section>
  );
}
