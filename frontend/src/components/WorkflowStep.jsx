import Card3D from "./Card3D";

export default function WorkflowStep({
  icon: Icon,
  stepNumber,
  title,
  description,
  glowColor = "emerald",
}) {
  return (
    <Card3D glowColor={glowColor} className="h-full border border-white/10 bg-slate-900/70 p-6 text-white backdrop-blur-xl">
      <div className="mb-4 flex items-center justify-between gap-3">
        <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 text-xs font-black text-slate-950 shadow-md shadow-emerald-500/30">
          0{stepNumber}
        </span>
        {Icon ? (
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-slate-800/80 text-emerald-400 border border-slate-700/60 shadow-xs">
            <Icon aria-hidden="true" className="h-5 w-5" />
          </span>
        ) : null}
      </div>
      <h3 className="text-base font-bold text-white tracking-tight">{title}</h3>
      <p className="mt-2.5 text-xs leading-relaxed text-slate-400">{description}</p>
    </Card3D>
  );
}


