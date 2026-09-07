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
      <label htmlFor={id} className="block text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
        {label}
      </label>
      <InputComponent
        id={id}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={error ? errorId : undefined}
        className="mt-2 w-full rounded-xl border border-white/15 bg-slate-900/90 px-4 py-3 text-sm text-white shadow-inner outline-none transition placeholder:text-slate-500 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
        {...props}
      />
      <ErrorMessage id={errorId} message={error} />
    </div>
  );
}


