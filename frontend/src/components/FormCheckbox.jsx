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
          className="mt-1 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-4 focus:ring-brand-100"
          {...props}
        />
        <div>
          <label htmlFor={id} className="text-sm font-semibold text-slate-800">
            {label}
          </label>
          {description ? (
            <p className="mt-1 text-sm leading-6 text-slate-600">
              {description}
            </p>
          ) : null}
        </div>
      </div>
      <ErrorMessage id={errorId} message={error} />
    </div>
  );
}

