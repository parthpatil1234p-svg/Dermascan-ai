import { CheckCircle2, Loader2 } from "lucide-react";

export default function LoadingIndicator({
  label = "Loading telemetry data...",
  stages,
  currentStageIndex = 0,
  progress,
  className = "",
}) {
  const safeStages = Array.isArray(stages) ? stages : [];

  // Simple spinner mode when no multi-step stages are passed
  if (safeStages.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center p-6 text-center ${className}`}>
        <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl border border-emerald-500/30 bg-emerald-500/10 shadow-[0_0_20px_rgba(16,185,129,0.25)]">
          <Loader2 className="h-7 w-7 animate-spin text-emerald-400" />
        </div>
        <p className="mt-4 font-mono text-xs font-bold uppercase tracking-wider text-emerald-400">
          {label}
        </p>
        {typeof progress === "number" && (
          <div className="mt-3 w-full max-w-xs">
            <div className="h-2 overflow-hidden rounded-full bg-slate-950 border border-white/10">
              <div
                className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-400 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="mt-1 block font-mono text-[10px] text-slate-400">{progress}%</span>
          </div>
        )}
      </div>
    );
  }

  // Multi-stage pipeline progress mode
  return (
    <div className={`rounded-3xl border border-white/10 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-2xl ${className}`}>
      {typeof progress === "number" && (
        <div className="mb-6">
          <div className="flex items-center justify-between text-xs font-mono font-bold uppercase tracking-wider text-emerald-400">
            <span>{label}</span>
            <span>{progress}%</span>
          </div>
          <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-slate-950 border border-white/10">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-400 transition-all duration-500 shadow-[0_0_12px_rgba(16,185,129,0.4)]"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      <ol className="space-y-3">
        {safeStages.map((stage, index) => {
          const isComplete = index < currentStageIndex;
          const isActive = index === currentStageIndex;

          return (
            <li
              key={stage}
              className={`flex items-center gap-3.5 rounded-2xl border p-3.5 transition-all ${
                isActive
                  ? "border-emerald-500/50 bg-emerald-950/40 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.15)]"
                  : isComplete
                  ? "border-white/5 bg-slate-950/40 text-slate-300"
                  : "border-white/5 bg-slate-950/20 text-slate-500"
              }`}
            >
              <span
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-xs font-black ${
                  isComplete
                    ? "bg-emerald-500/20 border border-emerald-500/40 text-emerald-400"
                    : isActive
                    ? "bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-md shadow-emerald-500/30"
                    : "bg-slate-800 text-slate-500"
                }`}
              >
                {isComplete ? (
                  <CheckCircle2 aria-hidden="true" className="h-4 w-4 text-emerald-400" />
                ) : (
                  index + 1
                )}
              </span>
              <span className="text-xs font-semibold">{stage}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
