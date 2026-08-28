import { Link } from "react-router-dom";

export default function PrimaryButton({
  children,
  className = "",
  icon: Icon,
  to,
  type = "button",
  ...props
}) {
  const classes = `inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-5 py-3 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 disabled:cursor-not-allowed disabled:bg-slate-300 ${className}`;

  if (to) {
    return (
      <Link to={to} className={classes} {...props}>
        {Icon ? <Icon aria-hidden="true" className="h-4 w-4" /> : null}
        {children}
      </Link>
    );
  }

  return (
    <button type={type} className={classes} {...props}>
      {Icon ? <Icon aria-hidden="true" className="h-4 w-4" /> : null}
      {children}
    </button>
  );
}

