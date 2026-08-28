export default function QualityMetricCard({ icon: Icon, label, status, detail, score }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-clinic-50 text-brand-700">
            <Icon className="h-5 w-5" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-slate-950">{label}</h3>
            <p className="mt-1 text-sm font-medium capitalize text-slate-700">
              {status.replaceAll("_", " ")}
            </p>
          </div>
        </div>
        <span className="shrink-0 text-sm font-bold text-brand-700">
          {score}/100
        </span>
      </div>
      {detail ? (
        <p className="mt-4 text-sm leading-6 text-slate-600">{detail}</p>
      ) : null}
    </article>
  );
}
