import { Printer } from "lucide-react";
import { useEffect } from "react";
import { useParams } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import FinalReportView from "../components/FinalReportView";
import LoadingIndicator from "../components/LoadingIndicator";
import { useFinalReport } from "../context/FinalReportContext";


export default function FinalReportPrintPage() {
  const { finalReportId } = useParams();
  const { finalReport, isLoading, error, loadReport } = useFinalReport();
  useEffect(() => { if (finalReport?.final_report_id !== finalReportId) loadReport(finalReportId).catch(() => {}); }, [finalReportId, finalReport?.final_report_id, loadReport]);
  if (isLoading || !finalReport || finalReport.final_report_id !== finalReportId) return <section className="px-4 py-16"><LoadingIndicator label="Preparing print view..." /><ErrorMessage message={error} /></section>;
  return <section className="px-4 py-8"><div className="print-hidden mx-auto mb-6 flex max-w-7xl justify-end"><button type="button" onClick={() => window.print()} className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white"><Printer className="h-4 w-4" aria-hidden="true" />Print Report</button></div><FinalReportView report={finalReport} printMode /></section>;
}
