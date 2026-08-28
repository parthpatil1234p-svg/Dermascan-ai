import { FileCheck2 } from "lucide-react";
import { useCallback, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import { FINAL_REPORT_STAGES } from "../constants/appContent";
import { useFinalReport } from "../context/FinalReportContext";
import { useUpload } from "../context/UploadContext";


export default function FinalReportGenerationPage() {
  const startedRef = useRef(false);
  const navigate = useNavigate();
  const { uploadId } = useUpload();
  const { generate, isGenerating, generationProgress, error } = useFinalReport();
  const start = useCallback(
    () => generate(uploadId).then((result) => navigate(`/reports/${result.final_report_id}`, { replace: true })).catch(() => {}),
    [generate, navigate, uploadId],
  );
  useEffect(() => { if (uploadId && !startedRef.current) { startedRef.current = true; start(); } }, [start, uploadId]);
  return <section className="px-4 py-14 sm:px-6"><PageHeader eyebrow="Versioned report snapshot" title="Generating Your Final Guidance Report" description="Validating trusted workflow reports and creating a reproducible snapshot without including your facial image." /><div className="mx-auto max-w-3xl border-y border-slate-200 py-8">
    {error ? <div className="text-center"><ErrorMessage message={error} /><PrimaryButton className="mt-5" icon={FileCheck2} onClick={start} disabled={isGenerating}>Try Again</PrimaryButton></div> : <div role="status"><div className="flex justify-between text-sm font-semibold text-slate-700"><span>Preparing report</span><span>{generationProgress}%</span></div><div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full bg-brand-600 transition-all" style={{ width: `${generationProgress}%` }} /></div><ol className="mt-6 grid gap-3 sm:grid-cols-2">{FINAL_REPORT_STAGES.map((stage) => <li key={stage} className="text-sm text-slate-700">{stage}</li>)}</ol></div>}
  </div></section>;
}
