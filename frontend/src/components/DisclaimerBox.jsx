import { AlertTriangle } from "lucide-react";
import { MEDICAL_DISCLAIMER } from "../constants/appContent";

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
