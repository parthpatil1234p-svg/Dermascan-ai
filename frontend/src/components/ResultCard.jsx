export default function ResultCard({ title, value, helper, children }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-wide text-brand-700">
        {title}
      </p>
      {value ? (
        <p className="mt-3 text-3xl font-bold text-slate-950">{value}</p>
      ) : null}
      {helper ? <p className="mt-2 text-sm text-slate-600">{helper}</p> : null}
      {children ? <div className="mt-5">{children}</div> : null}
    </article>
  );
}

