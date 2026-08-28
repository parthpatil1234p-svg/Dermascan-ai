export default function FeatureCard({ icon: Icon, title, description }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-soft">
      {Icon ? (
        <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-lg bg-clinic-100 text-clinic-700">
          <Icon aria-hidden="true" className="h-5 w-5" />
        </div>
      ) : null}
      <h3 className="text-lg font-semibold text-slate-950">{title}</h3>
      <p className="mt-3 text-sm leading-6 text-slate-600">{description}</p>
    </article>
  );
}

