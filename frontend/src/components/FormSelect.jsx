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
      <label htmlFor={id} className="block text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
        {label}
      </label>
      <select
        id={id}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={error ? errorId : undefined}
        className="mt-2 w-full rounded-xl border border-white/15 bg-slate-900 px-4 py-3 text-sm text-white shadow-inner outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
        {...props}
      >
        <option value="" className="bg-slate-900 text-slate-400">{placeholder}</option>
        {options.map((option) => {
          const value = typeof option === "string" ? option : option.value;
          const labelText = typeof option === "string" ? option : option.label;

          return (
            <option key={value} value={value} className="bg-slate-900 text-white">
              {labelText}
            </option>
          );
        })}
      </select>
      <ErrorMessage id={errorId} message={error} />
    </div>
  );
}


