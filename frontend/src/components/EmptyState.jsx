import SecondaryButton from "./SecondaryButton";

export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
      {Icon ? (
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
          <Icon aria-hidden="true" className="h-6 w-6" />
        </div>
      ) : null}
      <h2 className="text-xl font-semibold text-slate-950">{title}</h2>
      <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-slate-600">
        {description}
      </p>
      {action ? (
        <SecondaryButton to={action.to} className="mt-6">
          {action.label}
        </SecondaryButton>
      ) : null}
    </div>
  );
}

