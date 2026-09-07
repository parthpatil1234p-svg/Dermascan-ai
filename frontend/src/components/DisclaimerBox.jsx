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
      className={`mx-auto w-full max-w-5xl overflow-hidden rounded-xl border border-dashed border-slate-300 bg-slate-50/70 p-3 text-center ${className}`}
    >
      <span className="block mb-1 text-[10px] font-medium uppercase tracking-wider text-slate-400">
        Advertisement
      </span>
      <ins
        className="adsbygoogle"
        style={{ display: "block", minHeight: "90px" }}
        data-ad-client="ca-pub-1505656537844773"
        data-ad-slot={slot}
        data-ad-format={format}
        data-full-width-responsive={responsive}
      />
    </div>
  );
}

export default function DisclaimerBox({ title = "Medical disclaimer", description = MEDICAL_DISCLAIMER }) {
  return (
    <aside className="rounded-lg border border-amber-200 bg-amber-50 p-5 text-amber-950">
      <div className="flex items-start gap-3">
        <AlertTriangle
          aria-hidden="true"
          className="mt-0.5 h-5 w-5 shrink-0 text-amber-700"
        />
        <div>
          <h2 className="text-base font-semibold">{title}</h2>
          <p className="mt-2 text-sm leading-6">{description}</p>
        </div>
      </div>
    </aside>
  );
}
