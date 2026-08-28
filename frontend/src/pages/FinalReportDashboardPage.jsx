import { ArrowLeft, MessageSquareText } from "lucide-react";
import { useEffect } from "react";
import { useParams } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import FinalReportView from "../components/FinalReportView";
import LoadingIndicator from "../components/LoadingIndicator";
import SecondaryButton from "../components/SecondaryButton";
import { ROUTES } from "../constants/appContent";
import { useFinalReport } from "../context/FinalReportContext";


export default function FinalReportDashboardPage() {
  const { finalReportId } = useParams();
  const { finalReport, isLoading, isExporting, error, loadReport, exportPdf } = useFinalReport();
  useEffect(() => { if (finalReport?.final_report_id !== finalReportId) loadReport(finalReportId).catch(() => {}); }, [finalReportId, finalReport?.final_report_id, loadReport]);
  if (isLoading || !finalReport || finalReport.final_report_id !== finalReportId) return <section className="px-4 py-16"><LoadingIndicator label="Loading your final report..." />{error ? <div className="mx-auto mt-5 max-w-xl"><ErrorMessage message={error} /></div> : null}</section>;
  return <section className="px-4 py-10 sm:px-6 lg:px-8"><div className="print-hidden mx-auto mb-6 flex max-w-7xl flex-wrap gap-3"><SecondaryButton to={ROUTES.reports} icon={ArrowLeft}>Report History</SecondaryButton><SecondaryButton to={ROUTES.feedback} state={{ finalReportId, feedbackCategory: "report_feedback" }} icon={MessageSquareText}>Share Report Feedback</SecondaryButton></div><ErrorMessage message={error} /><FinalReportView report={finalReport} isExporting={isExporting} onExport={(mode) => exportPdf(finalReportId, mode).catch(() => {})} /></section>;
}
