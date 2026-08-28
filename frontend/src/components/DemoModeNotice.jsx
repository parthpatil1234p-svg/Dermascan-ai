import { FlaskConical } from "lucide-react";

export default function DemoModeNotice({ visible }) {
  if (!visible) return null;
  return (
    <aside
      className="rounded-lg border border-clinic-300 bg-clinic-50 p-4 text-clinic-950"
      role="status"
    >
      <div className="flex items-start gap-3">
        <FlaskConical className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
        <div>
          <h2 className="font-semibold">Demonstration Mode</h2>
          <p className="mt-1 text-sm leading-6">
            This result uses deterministic mock output for a college demonstration,
            not inference from an evaluated trained model.
          </p>
        </div>
      </div>
    </aside>
  );
}

