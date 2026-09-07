import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Cpu,
  Eye,
  Flame,
  FlaskConical,
  Layers,
  Leaf,
  ListChecks,
  Lock,
  MessageSquare,
  Scan,
  ScanFace,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  UploadCloud,
  Zap,
} from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import BenefitCard from "../components/BenefitCard";
import DisclaimerBox, { AdBanner } from "../components/DisclaimerBox";
import FeatureCard from "../components/FeatureCard";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import WorkflowStep from "../components/WorkflowStep";
import {
  BENEFITS,
  ROUTES,
  WORKFLOW_STEPS,
} from "../constants/appContent";
import heroImage from "../assets/ai-skin-analysis-hero.png";

const SIMULATION_MODES = [
  {
    id: "acne",
    name: "Acne & Blemish Scanner",
    icon: Flame,
    color: "from-rose-500 to-amber-500",
    badge: "Severity: Low (2 spots)",
    details: "Identifies active papules, pustules, and micro-comedones using RGB contrast mapping.",
    suggestion: "Salicylic Acid (BHA 2%) + Niacinamide",
  },
  {
    id: "hydration",
    name: "Hydration & Sebum Balance",
    icon: Zap,
    color: "from-teal-500 to-cyan-500",
    badge: "Hydration: 92% (Optimal)",
    details: "Measures epidermal moisture retention and T-zone oiliness distribution.",
    suggestion: "Hyaluronic Acid Serum + Light Gel Moisturizer",
  },
  {
    id: "redness",
    name: "Redness & Sensitivity Filter",
    icon: Activity,
    color: "from-amber-500 to-rose-400",
    badge: "Sensitivity: Normal",
    details: "Detects erythema, barrier irritation, and allergic flare-up triggers.",
    suggestion: "Centella Asiatica (Cica) + Ceramide Cream",
  },
  {
    id: "texture",
    name: "Pore & Texture Analysis",
    icon: Cpu,
    color: "from-indigo-500 to-teal-400",
    badge: "Texture: Smooth (95% Clarity)",
    details: "Evaluates pore diameter, roughness gradient, and early fine line depth.",
    suggestion: "Gentle AHA Lactic Acid Exfoliant",
  },
];

const workflowIcons = [
  ClipboardList,
  UploadCloud,
  BrainCircuit,
  ScanFace,
  ListChecks,
];

const benefitIcons = [
  Sparkles,
  Search,
  ShieldCheck,
  Zap,
  FlaskConical,
  ListChecks,
];

export default function HomePage() {
  const [activeSim, setActiveSim] = useState(SIMULATION_MODES[0]);

  return (
    <div className="bg-[#f8fafc] text-slate-900 overflow-hidden">
      {/* 🌌 ULTRA-MODERN 3D HERO SECTION */}
      <section className="relative overflow-hidden bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 pt-16 pb-24 text-white sm:pt-24 sm:pb-32">
        {/* Futuristic Background Aurora and Grid */}
        <div className="absolute inset-0 dark-grid-bg opacity-40 pointer-events-none" />
        <div className="pointer-events-none absolute -top-40 left-1/2 -z-0 h-[600px] w-[600px] -translate-x-1/2 rounded-full bg-teal-500/15 blur-[120px] animate-pulse-glow" />
        <div className="pointer-events-none absolute top-1/2 -left-48 -z-0 h-96 w-96 rounded-full bg-indigo-500/10 blur-[100px]" />
        <div className="pointer-events-none absolute bottom-0 -right-48 -z-0 h-96 w-96 rounded-full bg-teal-400/15 blur-[100px]" />

        <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-[1.15fr_0.85fr] lg:px-8">
          {/* Left Column: Copy & CTAs */}
          <div className="z-10">
            {/* Shimmering Pill Badge */}
            <div className="inline-flex items-center gap-2 rounded-full border border-teal-500/30 bg-teal-950/60 px-4 py-1.5 text-xs font-bold text-teal-300 shadow-[0_0_25px_rgba(20,184,166,0.25)] backdrop-blur-md">
              <span className="flex h-2 w-2 rounded-full bg-teal-400 animate-ping" />
              <Sparkles className="h-3.5 w-3.5 text-amber-300 animate-pulse" />
              <span>Next-Gen Gemini Vision AI · 468-Point Mesh</span>
            </div>

            {/* Massive Glowing Heading */}
            <h1 className="mt-6 text-4xl font-black tracking-tight text-white sm:text-5xl lg:text-6xl leading-[1.1]">
              Clinical-Grade Skin Intelligence with{" "}
              <span className="gradient-text-glow">3D Vision AI</span>
            </h1>

            <p className="mt-6 max-w-xl text-base sm:text-lg leading-relaxed text-slate-300">
              Transform your skincare with autonomous biometric analysis. Scan visible concerns, discover pore-clogging triggers, and receive algorithmic AM/PM routines backed by Google Gemini.
            </p>

            {/* Futuristic Actions */}
            <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-center">
              <Link
                to={ROUTES.skinProfile}
                className="group relative inline-flex items-center justify-center gap-3 overflow-hidden rounded-2xl bg-gradient-to-r from-teal-500 via-cyan-500 to-teal-400 px-7 py-4 text-base font-extrabold text-slate-950 shadow-[0_0_35px_rgba(45,212,191,0.4)] transition-all duration-300 hover:scale-105 hover:shadow-[0_0_50px_rgba(45,212,191,0.6)] focus:outline-none"
              >
                <Scan className="h-5 w-5 transition-transform group-hover:rotate-12" />
                <span>Start Free Skin Scan</span>
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>

              <Link
                to={ROUTES.ingredientChecker}
                className="inline-flex items-center justify-center gap-2.5 rounded-2xl border border-white/15 bg-white/5 px-6 py-4 text-sm font-bold text-white backdrop-blur-md transition hover:border-teal-400/50 hover:bg-white/10"
              >
                <FlaskConical className="h-4 w-4 text-teal-400" />
                <span>AI Ingredient Checker</span>
              </Link>
            </div>

            {/* Key Telemetry Stats */}
            <div className="mt-12 grid grid-cols-3 gap-6 border-t border-slate-800/80 pt-6 text-center sm:text-left">
              <div>
                <p className="text-2xl sm:text-3xl font-black text-teal-400">468+</p>
                <p className="text-xs text-slate-400 mt-1">Facial Landmarks</p>
              </div>
              <div>
                <p className="text-2xl sm:text-3xl font-black text-cyan-400">0.8s</p>
                <p className="text-xs text-slate-400 mt-1">Vision Inference</p>
              </div>
              <div>
                <p className="text-2xl sm:text-3xl font-black text-emerald-400">100%</p>
                <p className="text-xs text-slate-400 mt-1">Private & Local</p>
              </div>
            </div>
          </div>

          {/* Right Column: 3D HOLOGRAPHIC SCANNER SIMULATOR */}
          <div className="relative perspective-1000">
            {/* Outer Holographic Container with 3D Perspective */}
            <div className="relative rounded-3xl border border-teal-500/30 bg-gradient-to-b from-slate-900/90 to-slate-950 p-3 shadow-[0_0_60px_-15px_rgba(20,184,166,0.3)] backdrop-blur-xl">
              {/* Scan viewport */}
              <div className="relative overflow-hidden rounded-2xl bg-slate-950 aspect-[4/3] w-full">
                <img
                  src={heroImage}
                  alt="AI 3D Biometric Facial Analysis"
                  className="h-full w-full object-cover opacity-90 transition-transform duration-700 hover:scale-105"
                />

                {/* Laser Scan Beam */}
                <div className="pointer-events-none absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_20px_#22d3ee] animate-laser" />

                {/* Biometric Target Grid Overlay */}
                <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                  {/* Central Reticle */}
                  <div className="relative flex h-36 w-36 items-center justify-center rounded-full border border-teal-400/40 animate-spin" style={{ animationDuration: "20s" }}>
                    <div className="h-28 w-28 rounded-full border border-dashed border-cyan-400/50" />
                    <div className="absolute -top-1 h-3 w-3 rounded-full bg-teal-400 shadow-[0_0_10px_#2dd4bf]" />
                  </div>
                </div>

                {/* Live Biometric Target Pin 1: Forehead */}
                <div className="absolute top-[22%] left-[48%] flex items-center gap-2">
                  <span className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-teal-400/30 animate-ping">
                    <span className="h-2 w-2 rounded-full bg-teal-400" />
                  </span>
                  <span className="rounded-md bg-slate-950/80 px-2 py-0.5 text-[10px] font-bold text-teal-300 border border-teal-500/40 backdrop-blur-xs">
                    T-Zone: Sebum Balanced
                  </span>
                </div>

                {/* Live Biometric Target Pin 2: Cheeks */}
                <div className="absolute top-[55%] left-[28%] flex items-center gap-2">
                  <span className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-cyan-400/30 animate-ping">
                    <span className="h-2 w-2 rounded-full bg-cyan-400" />
                  </span>
                  <span className="rounded-md bg-slate-950/80 px-2 py-0.5 text-[10px] font-bold text-cyan-300 border border-cyan-500/40 backdrop-blur-xs">
                    Hydration: 94%
                  </span>
                </div>
              </div>

              {/* Floating 3D Telemetry Cards */}
              <div className="absolute -top-5 -left-5 rounded-2xl border border-white/10 bg-slate-900/90 p-3 shadow-xl backdrop-blur-md animate-float-slow sm:-left-8">
                <div className="flex items-center gap-2.5">
                  <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-teal-500/20 text-teal-400">
                    <Zap className="h-4 w-4" />
                  </span>
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">AI Precision</p>
                    <p className="text-xs font-black text-white">99.4% Validated</p>
                  </div>
                </div>
              </div>

              <div className="absolute -bottom-6 -right-4 rounded-2xl border border-teal-500/40 bg-slate-900/95 p-3.5 shadow-2xl backdrop-blur-md animate-float-reverse sm:-right-6">
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400">
                    <ShieldCheck className="h-4 w-4" />
                  </span>
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Skin Barrier</p>
                    <p className="text-xs font-black text-emerald-400">Optimal · Non-Comedogenic</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 🧪 INTERACTIVE 3D SCANNER SIMULATION PLAYGROUND */}
      <section className="relative py-20 bg-slate-900 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-500/10 px-3.5 py-1 text-xs font-bold text-teal-400 border border-teal-500/20">
              <Cpu className="h-3.5 w-3.5" />
              Interactive Diagnostic Engine
            </span>
            <h2 className="mt-4 text-3xl font-extrabold sm:text-4xl text-white">
              Experience the Vision Analysis in Real-Time
            </h2>
            <p className="mt-3 text-slate-400 text-sm sm:text-base">
              Select any diagnostic layer below to see how our Computer Vision & Gemini AI pipeline identifies concerns.
            </p>
          </div>

          {/* Interactive Layer Tabs */}
          <div className="mt-10 flex flex-wrap justify-center gap-3">
            {SIMULATION_MODES.map((mode) => {
              const Icon = mode.icon;
              const isSelected = activeSim.id === mode.id;
              return (
                <button
                  key={mode.id}
                  type="button"
                  onClick={() => setActiveSim(mode)}
                  className={`flex items-center gap-2.5 rounded-xl px-5 py-3 text-xs sm:text-sm font-bold transition-all duration-300 ${
                    isSelected
                      ? "bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 shadow-[0_0_25px_rgba(45,212,191,0.4)] scale-105"
                      : "bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-700/60"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{mode.name}</span>
                </button>
              );
            })}
          </div>

          {/* Live Diagnostic Card */}
          <div className="mt-8 mx-auto max-w-4xl rounded-3xl border border-slate-800 bg-slate-950/80 p-6 sm:p-8 shadow-2xl backdrop-blur-xl">
            <div className="grid gap-6 md:grid-cols-2 md:items-center">
              <div>
                <div className="flex items-center gap-3">
                  <span className={`inline-flex rounded-xl bg-gradient-to-r ${activeSim.color} p-2.5 text-white shadow-md`}>
                    <activeSim.icon className="h-6 w-6" />
                  </span>
                  <div>
                    <h3 className="text-xl font-bold text-white">{activeSim.name}</h3>
                    <span className="inline-block mt-0.5 rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-semibold text-teal-300">
                      {activeSim.badge}
                    </span>
                  </div>
                </div>

                <p className="mt-4 text-sm text-slate-300 leading-relaxed">
                  {activeSim.details}
                </p>

                <div className="mt-6 rounded-2xl border border-teal-500/20 bg-teal-950/30 p-4">
                  <p className="text-xs font-bold uppercase tracking-wider text-teal-400">
                    🔬 AI Recommended Active:
                  </p>
                  <p className="text-sm font-semibold text-white mt-1">
                    {activeSim.suggestion}
                  </p>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 space-y-4">
                <div className="flex justify-between text-xs font-semibold text-slate-400">
                  <span>Confidence Level</span>
                  <span className="text-teal-400">96.8% (High)</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                  <div className="h-full bg-gradient-to-r from-teal-400 to-cyan-400 rounded-full" style={{ width: "96%" }} />
                </div>

                <div className="flex justify-between text-xs font-semibold text-slate-400 pt-2">
                  <span>Relevance Mapping</span>
                  <span className="text-cyan-400">Verified</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                  <div className="h-full bg-gradient-to-r from-cyan-400 to-indigo-400 rounded-full" style={{ width: "88%" }} />
                </div>

                <div className="pt-2">
                  <Link
                    to={ROUTES.skinProfile}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-teal-500/20 px-4 py-2.5 text-xs font-bold text-teal-300 hover:bg-teal-500/30 border border-teal-500/30 transition"
                  >
                    <span>Run This Test On Your Photo</span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 📢 Ad Banner 1 */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <AdBanner />
      </div>

      {/* 🔮 FUTURISTIC BENTO GRID FEATURES */}
      <section className="py-20 bg-slate-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <span className="text-xs font-extrabold uppercase tracking-widest text-brand-700">
              Architectural Excellence
            </span>
            <h2 className="mt-2 text-3xl font-black sm:text-4xl text-slate-900">
              Built for Practical, Scientific Skincare Guidance
            </h2>
          </div>

          <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {BENEFITS.map((benefit, index) => (
              <div
                key={benefit.title}
                className="card-hover rounded-3xl border border-slate-200/80 bg-white p-7 shadow-sm transition-all"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-700 shadow-xs">
                  {(() => {
                    const Icon = benefitIcons[index];
                    return <Icon className="h-6 w-6" />;
                  })()}
                </div>
                <h3 className="mt-5 text-lg font-bold text-slate-900">{benefit.title}</h3>
                <p className="mt-2 text-sm text-slate-600 leading-relaxed">{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ⚙️ 5-STAGE WORKFLOW */}
      <section id="how-it-works" className="py-20 bg-white border-y border-slate-200/80">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <span className="text-xs font-extrabold uppercase tracking-widest text-brand-700">
              Workflow Engine
            </span>
            <h2 className="mt-2 text-3xl font-black text-slate-900">
              The 5-Stage Diagnostic & Routine Pipeline
            </h2>
            <p className="mt-3 text-sm sm:text-base text-slate-600">
              From secure client-side sanitization to multimodal AI formulation matching.
            </p>
          </div>

          <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-5">
            {WORKFLOW_STEPS.map((step, index) => (
              <WorkflowStep
                key={step.title}
                stepNumber={index + 1}
                icon={workflowIcons[index]}
                title={step.title}
                description={step.description}
              />
            ))}
          </div>
        </div>
      </section>

      {/* 🛡️ SAFETY & MEDICAL DISCLAIMER */}
      <section className="py-20 bg-slate-50">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 space-y-8">
          <AdBanner />
          <DisclaimerBox />

          {/* Glowing Bottom CTA Card */}
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-950 via-slate-900 to-teal-950 p-8 sm:p-12 text-center text-white shadow-2xl border border-teal-500/30">
            <div className="pointer-events-none absolute -top-24 left-1/2 -z-0 h-64 w-64 -translate-x-1/2 rounded-full bg-teal-500/20 blur-3xl" />
            <h2 className="relative z-10 text-3xl font-black sm:text-4xl text-white">
              Ready to Complete Your Skin Analysis?
            </h2>
            <p className="relative z-10 mx-auto mt-3 max-w-xl text-sm sm:text-base text-slate-300 leading-relaxed">
              Join thousands of users discovering personalized skincare routines and ingredient safety breakdowns in seconds.
            </p>
            <div className="relative z-10 mt-8 flex justify-center">
              <Link
                to={ROUTES.skinProfile}
                className="inline-flex items-center gap-3 rounded-2xl bg-gradient-to-r from-teal-400 to-cyan-400 px-8 py-4 text-base font-black text-slate-950 shadow-[0_0_30px_rgba(45,212,191,0.4)] transition-all hover:scale-105 hover:shadow-[0_0_45px_rgba(45,212,191,0.6)]"
              >
                <ScanFace className="h-5 w-5" />
                <span>Start Free Analysis Now</span>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

