import SecondaryButton from "./SecondaryButton";

export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="rounded-3xl border border-dashed border-white/15 bg-slate-900/60 p-10 text-center backdrop-blur-xl">
      {Icon ? (
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 shadow-inner">
          <Icon aria-hidden="true" className="h-7 w-7" />
        </div>
      ) : null}
      <h2 className="text-xl font-bold text-white">{title}</h2>
      {description ? (
        <p className="mx-auto mt-2.5 max-w-lg text-sm leading-relaxed text-slate-300">
          {description}
        </p>
      ) : null}
      {action ? (
        <div className="mt-6 flex justify-center">
          <SecondaryButton to={action.to}>
            {action.label}
          </SecondaryButton>
        </div>
      ) : null}
    </div>
  );
}


