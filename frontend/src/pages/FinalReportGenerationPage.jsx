import { FileCheck2, Loader2, Sparkles, ShieldCheck } from "lucide-react";
import { useCallback, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import Card3D from "../components/Card3D";
import { FINAL_REPORT_STAGES } from "../constants/appContent";
import { useFinalReport } from "../context/FinalReportContext";
import { useUpload } from "../context/UploadContext";

export default function FinalReportGenerationPage() {
  const startedRef = useRef(false);
  const navigate = useNavigate();
  const { uploadId } = useUpload();
  const { generate, isGenerating, generationProgress, error } = useFinalReport();

  const start = useCallback(() => {
    if (!uploadId) return;
    generate(uploadId)
      .then((result) => {
        if (result?.final_report_id) {
          navigate(`/reports/${result.final_report_id}`, { replace: true });
        }
      })
      .catch(() => {});
  }, [generate, navigate, uploadId]);

  useEffect(() => {
    if (uploadId && !startedRef.current) {
      startedRef.current = true;
      start();
    }
  }, [start, uploadId]);

  return (
    <section className="px-4 py-16 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <PageHeader
          eyebrow="Versioned 3D Telemetry Snapshot"
          title="Synthesizing Your Clinical Guidance Report"
          description="Aggregating validated AI skin classifications, visible concern observations, safety filters, and bespoke skincare regimens."
        />

        <div className="mt-8">
          {error ? (
            <Card3D glowColor="rose" className="border border-red-500/30 bg-slate-900/90 p-8 text-center backdrop-blur-2xl">
              <ErrorMessage message={error} />
              <div className="mt-6 flex justify-center">
                <PrimaryButton icon={FileCheck2} onClick={start} disabled={isGenerating}>
                  Retry Synthesis
                </PrimaryButton>
              </div>
            </Card3D>
          ) : (
            <Card3D glowColor="emerald" className="border border-white/10 bg-slate-900/90 p-8 sm:p-10 backdrop-blur-2xl">
              <div role="status">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Loader2 className="h-5 w-5 animate-spin text-emerald-400" />
                    <span className="font-mono text-xs uppercase tracking-widest text-emerald-400 font-bold">
                      Neural Snapshot Synthesis
                    </span>
                  </div>
                  <span className="font-mono text-sm font-extrabold text-white">
                    {generationProgress}%
                  </span>
                </div>

                <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-950 p-0.5 border border-white/10">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400 transition-all duration-300 shadow-[0_0_15px_rgba(16,185,129,0.5)]"
                    style={{ width: `${generationProgress}%` }}
                  />
                </div>

                <div className="mt-8 border-t border-white/10 pt-6">
                  <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 mb-4">
                    Validation Pipeline Stages:
                  </h3>
                  <ol className="grid gap-3 sm:grid-cols-2">
                    {FINAL_REPORT_STAGES.map((stage, idx) => (
                      <li
                        key={stage}
                        className="flex items-center gap-2.5 rounded-xl border border-white/5 bg-slate-950/50 p-3 text-xs text-slate-300"
                      >
                        <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
                        <span>{stage}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            </Card3D>
          )}
        </div>
      </div>
    </section>
  );
}

