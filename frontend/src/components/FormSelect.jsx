import ErrorMessage from "./ErrorMessage";

export default function FormSelect({
  id,
  label,
  options,
  placeholder = "Select an option",
  error,
  className = "",
  ...props
}) {
  const errorId = `${id}-error`;

  return (
    <div className={className}>
      <label htmlFor={id} className="block text-sm font-semibold text-slate-800">
        {label}
      </label>
      <select
        id={id}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={error ? errorId : undefined}
        className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-3 text-sm text-slate-950 shadow-sm outline-none transition focus:border-brand-600 focus:ring-4 focus:ring-brand-100"
        {...props}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => {
          const value = typeof option === "string" ? option : option.value;
          const labelText = typeof option === "string" ? option : option.label;

          return (
            <option key={value} value={value}>
              {labelText}
            </option>
          );
        })}
      </select>
      <ErrorMessage id={errorId} message={error} />
    </div>
  );
}

