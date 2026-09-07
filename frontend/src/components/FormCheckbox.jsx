import ErrorMessage from "./ErrorMessage";

export default function FormCheckbox({
  id,
  label,
  description,
  error,
  className = "",
  ...props
}) {
  const errorId = `${id}-error`;

  return (
    <div className={className}>
      <div className="flex items-start gap-3">
        <input
          id={id}
          type="checkbox"
          aria-invalid={error ? "true" : "false"}
          aria-describedby={error ? errorId : undefined}
          className="mt-1 h-4 w-4 rounded border-white/20 bg-slate-900 text-emerald-500 focus:ring-2 focus:ring-emerald-500/30"
          {...props}
        />
        <div>
          <label htmlFor={id} className="text-sm font-semibold text-white">
            {label}
          </label>
          {description ? (
            <p className="mt-0.5 text-xs leading-relaxed text-slate-300">
              {description}
            </p>
          ) : null}
        </div>
      </div>
      <ErrorMessage id={errorId} message={error} />
    </div>
  );
}


