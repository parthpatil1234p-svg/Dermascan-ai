/**
 * BiometricGauge3D - 3D Futuristic Concentric Circular Metric Gauge
 */
export default function BiometricGauge3D({
  score = 94,
  label = "Skin Health Index",
  grade = "Optimal",
  size = 140,
  strokeWidth = 10,
  color = "emerald", // "emerald" | "cyan" | "amber" | "rose"
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const colorMap = {
    emerald: {
      stroke: "#10B981",
      glow: "rgba(16, 185, 129, 0.4)",
      badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    },
    cyan: {
      stroke: "#06B6D4",
      glow: "rgba(6, 182, 212, 0.4)",
      badge: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
    },
    amber: {
      stroke: "#F59E0B",
      glow: "rgba(245, 158, 11, 0.4)",
      badge: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    },
    rose: {
      stroke: "#F43F5E",
      glow: "rgba(244, 63, 94, 0.4)",
      badge: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    },
  };

  const theme = colorMap[color] || colorMap.emerald;

  return (
    <div className="relative flex flex-col items-center justify-center p-4">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        {/* Outer ambient glow ring */}
        <div
          className="absolute inset-2 rounded-full blur-lg opacity-40 animate-pulse"
          style={{ background: theme.glow }}
        />

        <svg width={size} height={size} className="rotate-[-90deg] transform">
          {/* Background Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-slate-200 dark:text-slate-800"
            fill="transparent"
          />
          {/* Animated Value Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={theme.stroke}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            fill="transparent"
            style={{
              transition: "stroke-dashoffset 1.5s cubic-bezier(0.2, 0.8, 0.2, 1)",
              filter: `drop-shadow(0px 0px 8px ${theme.glow})`,
            }}
          />
        </svg>

        {/* Center Readout */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-3xl font-black tracking-tight text-slate-900 dark:text-white">
            {score}
            <span className="text-sm font-semibold text-slate-400">%</span>
          </span>
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">
            {grade}
          </span>
        </div>
      </div>

      {label && (
        <span className={`mt-3 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${theme.badge}`}>
          {label}
        </span>
      )}
    </div>
  );
}
