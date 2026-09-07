import { Link } from "react-router-dom";

export default function SecondaryButton({
  children,
  className = "",
  icon: Icon,
  to,
  type = "button",
  ...props
}) {
  const classes = `inline-flex items-center justify-center gap-2 rounded-xl border border-white/15 bg-slate-900/80 px-5 py-2.5 text-xs font-bold text-white shadow-sm backdrop-blur-md transition-all duration-200 hover:border-emerald-500/50 hover:bg-slate-800 hover:text-emerald-300 hover:shadow-[0_0_15px_rgba(16,185,129,0.2)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500 disabled:cursor-not-allowed disabled:border-white/5 disabled:bg-slate-950 disabled:text-slate-600 ${className}`;

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


