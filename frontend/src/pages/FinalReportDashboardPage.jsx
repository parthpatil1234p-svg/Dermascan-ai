import { ArrowLeft, MessageSquareText, ShieldAlert } from "lucide-react";
import { useEffect } from "react";
import { useParams } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import FinalReportView from "../components/FinalReportView";
import LoadingIndicator from "../components/LoadingIndicator";
import SecondaryButton from "../components/SecondaryButton";
import Card3D from "../components/Card3D";
import { ROUTES } from "../constants/appContent";
import { useFinalReport } from "../context/FinalReportContext";

export default function FinalReportDashboardPage() {
  const { finalReportId } = useParams();
  const { finalReport, isLoading, isExporting, error, loadReport, exportPdf } = useFinalReport();

  useEffect(() => {
    if (finalReport?.final_report_id !== finalReportId) {
      loadReport(finalReportId).catch(() => {});
    }
  }, [finalReportId, finalReport?.final_report_id, loadReport]);

  if (isLoading || !finalReport || finalReport.final_report_id !== finalReportId) {
    return (
      <section className="px-4 py-20">
        <div className="mx-auto max-w-md">
          <Card3D glowColor="emerald" className="border border-white/10 bg-slate-900/80 p-8 text-center backdrop-blur-2xl">
            <LoadingIndicator label="Assembling high-resolution telemetry report..." />
            {error ? (
              <div className="mt-5">
                <ErrorMessage message={error} />
              </div>
            ) : null}
          </Card3D>
        </div>
      </section>
    );
  }

  return (
    <section className="px-4 py-10 sm:px-6 lg:px-8">
      <div className="print-hidden mx-auto mb-8 flex max-w-7xl flex-wrap items-center justify-between gap-4">
        <SecondaryButton to={ROUTES.reports} icon={ArrowLeft}>
          Report Archive
        </SecondaryButton>
        <SecondaryButton
          to={ROUTES.feedback}
          state={{ finalReportId, feedbackCategory: "report_feedback" }}
          icon={MessageSquareText}
        >
          Share Clinical Feedback
        </SecondaryButton>
      </div>

      <ErrorMessage message={error} />
      <FinalReportView
        report={finalReport}
        isExporting={isExporting}
        onExport={(mode) => exportPdf(finalReportId, mode).catch(() => {})}
      />
    </section>
  );
}

