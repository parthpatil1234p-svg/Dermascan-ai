import { AlertTriangle } from "lucide-react";
import { useEffect } from "react";
import { MEDICAL_DISCLAIMER } from "../constants/appContent";

export function AdBanner({
  slot = "1234567890",
  format = "auto",
  responsive = "true",
  className = "my-6",
}) {
  useEffect(() => {
    try {
      if (typeof window !== "undefined") {
        (window.adsbygoogle = window.adsbygoogle || []).push({});
      }
    } catch (err) {
      console.error("AdSense error:", err);
    }
  }, []);

  return (
    <div
      className={`mx-auto w-full max-w-5xl overflow-hidden rounded-2xl border border-dashed border-white/15 bg-slate-900/60 p-3 text-center backdrop-blur-md ${className}`}
    >
      <span className="block mb-1 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
        Advertisement
      </span>
      <ins
        className="adsbygoogle"
        style={{ display: "block", minHeight: "90px" }}
        data-ad-client="ca-pub-1505568687844779"
        data-ad-slot={slot}
        data-ad-format={format}
        data-full-width-responsive={responsive}
      />
    </div>
  );
}

export default function DisclaimerBox({ title = "Medical Disclaimer", description = MEDICAL_DISCLAIMER }) {
  return (
    <aside className="rounded-2xl border border-amber-500/30 bg-amber-950/30 p-5 text-amber-200 backdrop-blur-xl">
      <div className="flex items-start gap-3.5">
        <AlertTriangle
          aria-hidden="true"
          className="mt-0.5 h-5 w-5 shrink-0 text-amber-400"
        />
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wide text-amber-300">{title}</h2>
          <p className="mt-2 text-xs leading-relaxed text-amber-100/90">{description}</p>
        </div>
      </div>
    </aside>
  );
}

