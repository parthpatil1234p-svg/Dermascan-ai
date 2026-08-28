import ErrorMessage from "./ErrorMessage";

export default function FormInput({
  id,
  label,
  error,
  className = "",
  as = "input",
  ...props
}) {
  const InputComponent = as === "textarea" ? "textarea" : "input";
  const errorId = `${id}-error`;

  return (
    <div className={className}>
      <label htmlFor={id} className="block text-sm font-semibold text-slate-800">
        {label}
      </label>
      <InputComponent
        id={id}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={error ? errorId : undefined}
        className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-3 text-sm text-slate-950 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-600 focus:ring-4 focus:ring-brand-100"
        {...props}
      />
      <ErrorMessage id={errorId} message={error} />
    </div>
  );
}

