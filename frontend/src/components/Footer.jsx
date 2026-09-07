import { Activity, FlaskConical, Lock, ScanFace, ShieldCheck, Sparkles, Zap } from "lucide-react";
import { Link } from "react-router-dom";
import { APP_NAME, MEDICAL_DISCLAIMER, ROUTES } from "../constants/appContent";

const quickLinks = [
  { label: "Home Dashboard", to: ROUTES.home },
  { label: "AI Ingredient Safety Checker", to: ROUTES.ingredientChecker },
  { label: "Product Catalogue", to: ROUTES.products },
  { label: "Start Biometric Scan", to: ROUTES.skinProfile },
  { label: "Diagnostic Reports", to: ROUTES.reports },
];

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="relative overflow-hidden border-t border-white/10 bg-slate-950 text-slate-400">
      {/* Background Cyber Grid */}
      <div className="cyber-grid pointer-events-none absolute inset-0 opacity-15" />
      <div className="pointer-events-none absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-emerald-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -top-24 -right-24 h-72 w-72 rounded-full bg-cyan-500/10 blur-3xl" />

      {/* Live System Status Strip */}
      <div className="relative border-b border-white/10 bg-slate-900/60 px-4 py-3 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
              <span className="font-semibold text-slate-300">Gemini Multimodal Vision Engine</span>
              <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 font-bold text-emerald-400 border border-emerald-500/20">Operational</span>
            </div>
            <div className="hidden sm:flex items-center gap-2 text-slate-400">
              <Zap className="h-3.5 w-3.5 text-cyan-400" />
              <span>Inference Latency: ~0.4s</span>
            </div>
          </div>

          <div className="flex items-center gap-4 text-slate-400">
            <div className="flex items-center gap-1.5">
              <Lock className="h-3.5 w-3.5 text-emerald-400" />
              <span>Zero-Storage Facial Privacy</span>
            </div>
            <span className="hidden sm:inline font-mono text-[11px] text-slate-400">v2.4.0-Production</span>
          </div>
        </div>
      </div>

      <div className="relative mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 md:grid-cols-[1.2fr_0.8fr_1fr] lg:px-8">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-cyan-500 text-slate-950 font-black shadow-md shadow-emerald-500/30">
              <ScanFace className="h-5 w-5" />
            </div>
            <p className="text-lg font-black tracking-tight text-white">{APP_NAME}</p>
          </div>
          <p className="mt-4 max-w-sm text-xs leading-6 text-slate-400">
            Next-generation autonomous dermatology intelligence. Combines computer vision landmarking with Google Gemini multimodal reasoning for clinical-grade cosmetic skincare guidance.
          </p>
          <div className="mt-5 flex items-center gap-3">
            <span className="rounded-lg bg-slate-900 px-3 py-1.5 text-[11px] font-bold text-emerald-400 border border-slate-800">
              ⚡ 468 3D Mesh Nodes
            </span>
            <span className="rounded-lg bg-slate-900 px-3 py-1.5 text-[11px] font-bold text-cyan-400 border border-slate-800">
              🧪 10k+ Ingredients
            </span>
          </div>
        </div>

        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Quick Navigation
          </h2>
          <ul className="mt-4 space-y-2.5">
            {quickLinks.map((link) => (
              <li key={link.label}>
                <Link
                  to={link.to}
                  className="text-xs font-medium text-slate-400 transition hover:text-emerald-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-500"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            Medical Disclaimer & Privacy
          </h2>
          <p className="mt-4 text-xs leading-relaxed text-slate-400">
            {MEDICAL_DISCLAIMER}
          </p>
          <p className="mt-3 text-[11px] text-slate-400">
            © {currentYear} {APP_NAME}. All rights reserved. Created for educational & research purposes.
          </p>
        </div>
      </div>
    </footer>
  );
}

