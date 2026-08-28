import ErrorMessage from "./ErrorMessage";

export default function FormRadioGroup({
  legend,
  name,
  options,
  value,
  onChange,
  error,
  className = "",
}) {
  const errorId = `${name}-error`;

  return (
    <fieldset
      className={className}
      aria-invalid={error ? "true" : "false"}
      aria-describedby={error ? errorId : undefined}
    >
      <legend className="block text-sm font-semibold text-slate-800">
        {legend}
      </legend>
      <div className="mt-3 grid gap-3 sm:grid-cols-3">
        {options.map((option) => (
          <label
            key={option}
            className="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-300 bg-white px-3 py-3 text-sm font-medium text-slate-700 shadow-sm transition has-[:checked]:border-brand-600 has-[:checked]:bg-brand-50 has-[:checked]:text-brand-700"
          >
            <input
              type="radio"
              name={name}
              value={option}
              checked={value === option}
              onChange={(event) => onChange(event.target.value)}
              className="h-4 w-4 border-slate-300 text-brand-600 focus:ring-4 focus:ring-brand-100"
            />
            {option}
          </label>
        ))}
      </div>
      <ErrorMessage id={errorId} message={error} />
    </fieldset>
  );
}

