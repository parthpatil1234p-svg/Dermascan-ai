import Card3D from "./Card3D";

export default function BenefitCard({ icon: Icon, title, description, glowColor = "emerald" }) {
  return (
    <Card3D glowColor={glowColor} className="h-full border border-white/10 bg-slate-900/70 p-6 text-white backdrop-blur-xl">
      <div className="flex items-start gap-4">
        {Icon ? (
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-tr from-emerald-500/20 to-teal-500/10 text-emerald-400 border border-emerald-500/30 shadow-md shadow-emerald-500/10">
            <Icon aria-hidden="true" className="h-6 w-6" />
          </div>
        ) : null}
        <div>
          <h3 className="text-base font-bold text-white tracking-tight">{title}</h3>
          <p className="mt-2 text-xs leading-relaxed text-slate-300">
            {description}
          </p>
        </div>
      </div>
    </Card3D>
  );
}


