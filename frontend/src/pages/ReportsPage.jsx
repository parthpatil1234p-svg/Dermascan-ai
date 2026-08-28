import { Archive, CalendarDays, Download, Eye, FileText, Printer } from "lucide-react";
import { useEffect } from "react";
import EmptyState from "../components/EmptyState";
import ErrorMessage from "../components/ErrorMessage";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import { ROUTES } from "../constants/appContent";
import { useFinalReport } from "../context/FinalReportContext";


export default function ReportsPage() {
  const { reportHistory, pagination, isLoading, isExporting, error, loadHistory, archive, exportPdf } = useFinalReport();
  useEffect(() => { loadHistory({ page: 1, page_size: 12, sort: "newest" }).catch(() => {}); }, [loadHistory]);
  return <section className="px-4 py-14 sm:px-6 lg:px-8"><PageHeader eyebrow="Owner-protected history" title="Final Report History" description="View, print, export, or archive versioned guidance reports without exposing facial images or private identifiers." /><div className="mx-auto max-w-7xl"><ErrorMessage message={error} />
    {isLoading && !reportHistory.length ? <p className="text-center text-sm font-semibold text-brand-700" role="status">Loading report history...</p> : null}
    {!isLoading && !reportHistory.length ? <EmptyState icon={FileText} title="No final reports yet" description="Complete the analysis, recommendation, and routine workflow to generate a versioned final report." action={{ label: "Start Analysis", to: ROUTES.faceScan }} /> : <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">{reportHistory.map((report) => <article key={report.final_report_id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-bold text-brand-700">{report.final_report_id}</p><h2 className="mt-2 text-xl font-bold text-slate-950">{report.skin_type}</h2></div><span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-bold text-slate-700">v{report.report_version} · {report.report_status.replaceAll("_", " ")}</span></div><div className="mt-4 flex items-center gap-2 text-sm text-slate-600"><CalendarDays className="h-4 w-4" aria-hidden="true" />{new Date(report.analysis_date).toLocaleDateString("en-IN")}</div><p className="mt-4 text-sm text-slate-700">{report.main_visible_observations.join(", ") || "No observed characteristic summary"}</p><p className="mt-2 text-xs text-slate-500">Routine: {report.routine_status}</p><div className="mt-5 grid grid-cols-2 gap-2"><SecondaryButton to={`/reports/${report.final_report_id}`} icon={Eye}>View</SecondaryButton><SecondaryButton to={`/reports/${report.final_report_id}/print`} icon={Printer}>Print</SecondaryButton><SecondaryButton type="button" icon={Download} disabled={isExporting} onClick={() => exportPdf(report.final_report_id, "standard").catch(() => {})}>PDF</SecondaryButton><SecondaryButton type="button" icon={Archive} onClick={() => archive(report.final_report_id).catch(() => {})}>Archive</SecondaryButton></div></article>)}</div>}
    {pagination?.has_next ? <div className="mt-7 text-center"><PrimaryButton onClick={() => loadHistory({ page: pagination.page + 1, page_size: 12 }).catch(() => {})}>Next Page</PrimaryButton></div> : null}
  </div></section>;
}
