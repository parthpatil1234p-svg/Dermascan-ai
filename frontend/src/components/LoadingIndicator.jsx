import { CheckCircle2 } from "lucide-react";

export default function LoadingIndicator({ stages, currentStageIndex, progress }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-soft">
      <div className="mb-6">
        <div className="flex items-center justify-between gap-4 text-sm font-semibold text-slate-700">
          <span>Temporary UI simulation</span>
          <span>{progress}%</span>
        </div>
        <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-brand-600 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <ol className="space-y-4">
        {stages.map((stage, index) => {
          const isComplete = index < currentStageIndex;
          const isActive = index === currentStageIndex;

          return (
            <li
              key={stage}
              className={`flex items-center gap-3 rounded-lg border p-4 ${
                isActive
                  ? "border-brand-500 bg-brand-50 text-brand-700"
                  : "border-slate-200 bg-white text-slate-600"
              }`}
            >
              <span
                className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold ${
                  isComplete
                    ? "bg-leaf-500 text-white"
                    : isActive
                      ? "bg-brand-600 text-white"
                      : "bg-slate-100 text-slate-500"
                }`}
              >
                {isComplete ? (
                  <CheckCircle2 aria-hidden="true" className="h-5 w-5" />
                ) : (
                  index + 1
                )}
              </span>
              <span className="font-medium">{stage}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

