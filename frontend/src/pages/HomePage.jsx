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
import Card3D from "../components/Card3D";
import BiometricGauge3D from "../components/BiometricGauge3D";
import ThreeDimensionMeshCanvas from "../components/ThreeDimensionMeshCanvas";
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
    name: "Acne & Comedone Mapping",
    icon: Flame,
    color: "rose",
    badge: "Severity: Low (2 Micro-spots)",
    score: 91,
    details: "Performs high-frequency sub-surface chromatic contrast evaluation to detect active papules, pustules, and micro-comedones before surface emergence.",
    suggestion: "Salicylic Acid (BHA 2%) + 5% Niacinamide Solution",
  },
  {
    id: "hydration",
    name: "Hydration & Barrier Index",
    icon: Zap,
    color: "emerald",
    badge: "Hydration: 94% (Optimal)",
    score: 94,
    details: "Calculates stratum corneum water-binding retention capacity and T-zone vs U-zone sebum equilibrium.",
    suggestion: "Multi-Molecular Hyaluronic Acid + Ceramide Complex",
  },
  {
    id: "redness",
    name: "Vascular Erythema & Sensitivity",
    icon: Activity,
    color: "amber",
    badge: "Barrier Sensitivity: Resilient",
    score: 88,
    details: "Assesses micro-capillary flushing, trans-epidermal moisture loss (TEWL), and allergen reaction propensity.",
    suggestion: "Centella Asiatica (Cica) + Madecassoside Barrier Cream",
  },
  {
    id: "texture",
    name: "Pore Topography & Clarity",
    icon: Cpu,
    color: "cyan",
    badge: "Pore Clarity: 96% Clear",
    score: 96,
    details: "Evaluates surface micro-relief, follicular diameter variance, and epidermal cellular turnover rate.",
    suggestion: "Lactic Acid (AHA 5%) + Micro-Algae Radiance Peptides",
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
    <div className="relative bg-slate-950 text-slate-100 overflow-hidden">
      {/* 🌌 ULTRA-MODERN 3D HERO SECTION */}
      <section className="relative min-h-[90vh] overflow-hidden pt-12 pb-24 text-white sm:pt-20 sm:pb-32 flex items-center">
        {/* Interactive 3D Canvas Background */}
        <ThreeDimensionMeshCanvas mode="hero" nodeCount={50} className="opacity-40" />

        {/* Ambient Glows */}
        <div className="pointer-events-none absolute -top-40 left-1/2 -z-0 h-[650px] w-[650px] -translate-x-1/2 rounded-full bg-emerald-500/15 blur-[140px] animate-pulse-glow" />
        <div className="pointer-events-none absolute top-1/3 -left-48 -z-0 h-96 w-96 rounded-full bg-cyan-500/10 blur-[120px]" />
        <div className="pointer-events-none absolute bottom-10 -right-48 -z-0 h-96 w-96 rounded-full bg-emerald-400/10 blur-[120px]" />

        <div className="relative z-10 mx-auto grid max-w-7xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-[1.15fr_0.85fr] lg:px-8">
          {/* Left Column: Copy & CTAs */}
          <div>
            {/* Shimmering Pill Badge */}
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-950/60 px-4 py-1.5 text-xs font-bold text-emerald-300 shadow-[0_0_25px_rgba(16,185,129,0.25)] backdrop-blur-md">
              <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
              <Sparkles className="h-3.5 w-3.5 text-amber-300 animate-pulse" />
              <span>Multimodal Vision AI · 468-Point Mesh Landmarking</span>
            </div>

            {/* Massive Glowing Heading */}
            <h1 className="mt-6 text-4xl font-black tracking-tight text-white sm:text-5xl lg:text-6xl leading-[1.08]">
              Precision Skin Diagnostics with{" "}
              <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
                3D Spatial AI
              </span>
            </h1>

            <p className="mt-6 max-w-xl text-sm sm:text-base leading-relaxed text-slate-300">
              Autonomous clinical dermatology intelligence. Map acne severity, evaluate moisture barriers, verify cosmetic formulation conflicts, and generate tailored AM/PM routines using Gemini AI.
            </p>

            {/* Futuristic 3D Actions */}
            <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-center">
              <Link
                to={ROUTES.skinProfile}
                className="group relative inline-flex items-center justify-center gap-3 overflow-hidden rounded-2xl bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400 px-8 py-4 text-base font-black text-slate-950 shadow-[0_0_35px_rgba(16,185,129,0.45)] transition-all duration-300 hover:scale-105 hover:shadow-[0_0_55px_rgba(16,185,129,0.65)] focus:outline-none"
              >
                <Scan className="h-5 w-5 transition-transform group-hover:rotate-12" />
                <span>Start Free 3D Analysis</span>
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1.5" />
              </Link>

              <Link
                to={ROUTES.ingredientChecker}
                className="inline-flex items-center justify-center gap-2.5 rounded-2xl border border-white/15 bg-slate-900/80 px-6 py-4 text-sm font-bold text-white backdrop-blur-md transition hover:border-emerald-400/50 hover:bg-slate-800"
              >
                <FlaskConical className="h-4 w-4 text-emerald-400" />
                <span>AI Ingredient Checker</span>
              </Link>
            </div>

            {/* Key Telemetry Stats */}
            <div className="mt-12 grid grid-cols-3 gap-6 border-t border-slate-800/80 pt-6 text-center sm:text-left">
              <div>
                <p className="text-2xl sm:text-3xl font-black text-emerald-400">468</p>
                <p className="text-xs text-slate-400 mt-1">Biometric Nodes</p>
              </div>
              <div>
                <p className="text-2xl sm:text-3xl font-black text-cyan-400">&lt;0.4s</p>
                <p className="text-xs text-slate-400 mt-1">Vision Inference</p>
              </div>
              <div>
                <p className="text-2xl sm:text-3xl font-black text-teal-300">100%</p>
                <p className="text-xs text-slate-400 mt-1">Private Sanitation</p>
              </div>
            </div>
          </div>

          {/* Right Column: 3D HOLOGRAPHIC SCANNER SIMULATOR */}
          <div className="relative perspective-1000">
            <Card3D glowColor="emerald" className="border-emerald-500/30 bg-slate-900/90 p-3 shadow-2xl backdrop-blur-2xl">
              {/* Scan viewport */}
              <div className="relative overflow-hidden rounded-2xl bg-slate-950 aspect-[4/3] w-full">
                <img
                  src={heroImage}
                  alt="AI 3D Biometric Facial Analysis"
                  className="h-full w-full object-cover opacity-90 transition-transform duration-700 hover:scale-105"
                />

                {/* Laser Scan Beam */}
                <div className="pointer-events-none absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_20px_#10b981] animate-laser" />

                {/* Biometric Target Grid Overlay */}
                <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                  <div className="relative flex h-36 w-36 items-center justify-center rounded-full border border-emerald-400/40 animate-spin" style={{ animationDuration: "18s" }}>
                    <div className="h-28 w-28 rounded-full border border-dashed border-cyan-400/50" />
                    <div className="absolute -top-1 h-3 w-3 rounded-full bg-emerald-400 shadow-[0_0_12px_#10b981]" />
                  </div>
                </div>

                {/* Live Biometric Target Pin 1: Forehead */}
                <div className="absolute top-[22%] left-[48%] flex items-center gap-2">
                  <span className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-emerald-400/30 animate-ping">
                    <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  </span>
                  <span className="rounded-md bg-slate-950/85 px-2 py-0.5 text-[10px] font-bold text-emerald-300 border border-emerald-500/40 backdrop-blur-xs">
                    T-Zone: Sebum Balanced
                  </span>
                </div>

                {/* Live Biometric Target Pin 2: Cheeks */}
                <div className="absolute top-[55%] left-[28%] flex items-center gap-2">
                  <span className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-cyan-400/30 animate-ping">
                    <span className="h-2 w-2 rounded-full bg-cyan-400" />
                  </span>
                  <span className="rounded-md bg-slate-950/85 px-2 py-0.5 text-[10px] font-bold text-cyan-300 border border-cyan-500/40 backdrop-blur-xs">
                    Hydration: 94%
                  </span>
                </div>
              </div>

              {/* Floating Telemetry Stats */}
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-xl border border-white/10 bg-slate-950/80 p-2.5 flex items-center gap-2">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400">
                    <Zap className="h-3.5 w-3.5" />
                  </span>
                  <div>
                    <p className="text-[9px] uppercase font-bold text-slate-400">Precision Score</p>
                    <p className="text-xs font-black text-white">99.4% Validated</p>
                  </div>
                </div>
                <div className="rounded-xl border border-white/10 bg-slate-950/80 p-2.5 flex items-center gap-2">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-cyan-500/20 text-cyan-400">
                    <ShieldCheck className="h-3.5 w-3.5" />
                  </span>
                  <div>
                    <p className="text-[9px] uppercase font-bold text-slate-400">Safety Index</p>
                    <p className="text-xs font-black text-cyan-300">Hypoallergenic</p>
                  </div>
                </div>
              </div>
            </Card3D>
          </div>
        </div>
      </section>

      {/* 🧪 INTERACTIVE 3D SCANNER SIMULATION PLAYGROUND */}
      <section className="relative py-20 bg-slate-900/90 text-white border-y border-white/10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3.5 py-1 text-xs font-bold text-emerald-400 border border-emerald-500/20">
              <Cpu className="h-3.5 w-3.5" />
              Spatial Diagnostic Engine
            </span>
            <h2 className="mt-4 text-3xl font-extrabold sm:text-4xl text-white">
              Experience Real-Time Biometric Analysis
            </h2>
            <p className="mt-3 text-slate-400 text-sm sm:text-base">
              Switch between diagnostic layer modes to see how our Computer Vision & Gemini AI pipeline identifies concerns.
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
                      ? "bg-gradient-to-r from-emerald-500 to-teal-400 text-slate-950 shadow-[0_0_25px_rgba(16,185,129,0.45)] scale-105"
                      : "bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-700/60"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{mode.name}</span>
                </button>
              );
            })}
          </div>

          {/* Live Diagnostic 3D Card with Biometric Gauge */}
          <div className="mt-10 mx-auto max-w-4xl">
            <Card3D glowColor={activeSim.color === "rose" ? "violet" : activeSim.color === "cyan" ? "cyan" : "emerald"} className="border-white/10 bg-slate-950/90 p-6 sm:p-8 backdrop-blur-2xl">
              <div className="grid gap-8 md:grid-cols-[1.3fr_0.7fr] md:items-center">
                <div>
                  <div className="flex items-center gap-3">
                    <span className="inline-flex rounded-xl bg-emerald-500/20 p-2.5 text-emerald-400 border border-emerald-500/30">
                      <activeSim.icon className="h-6 w-6" />
                    </span>
                    <div>
                      <h3 className="text-xl font-bold text-white">{activeSim.name}</h3>
                      <span className="inline-block mt-0.5 rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-semibold text-emerald-300 border border-slate-700">
                        {activeSim.badge}
                      </span>
                    </div>
                  </div>

                  <p className="mt-4 text-xs sm:text-sm text-slate-300 leading-relaxed">
                    {activeSim.details}
                  </p>

                  <div className="mt-6 rounded-2xl border border-emerald-500/20 bg-emerald-950/30 p-4">
                    <p className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                      🔬 Target Formulation:
                    </p>
                    <p className="text-sm font-semibold text-white mt-1">
                      {activeSim.suggestion}
                    </p>
                  </div>
                </div>

                <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/90 p-4">
                  <BiometricGauge3D
                    score={activeSim.score}
                    label={activeSim.name}
                    grade="Optimal"
                    color={activeSim.color}
                    size={150}
                  />

                  <Link
                    to={ROUTES.skinProfile}
                    className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-500/20 px-4 py-2.5 text-xs font-bold text-emerald-300 hover:bg-emerald-500/30 border border-emerald-500/30 transition"
                  >
                    <span>Run Scan On Your Photo</span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            </Card3D>
          </div>
        </div>
      </section>

      {/* 📢 Ad Banner 1 */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <AdBanner />
      </div>

      {/* 🔮 3D TILT BENTO GRID FEATURES */}
      <section className="py-20 bg-slate-950">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <span className="text-xs font-extrabold uppercase tracking-widest text-emerald-400">
              Architectural Capabilities
            </span>
            <h2 className="mt-2 text-3xl font-black sm:text-4xl text-white">
              Clinical Intelligence Meets Modern Dermatology
            </h2>
          </div>

          <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {BENEFITS.map((benefit, index) => (
              <BenefitCard
                key={benefit.title}
                title={benefit.title}
                description={benefit.description}
                icon={benefitIcons[index]}
                glowColor={index % 2 === 0 ? "emerald" : "cyan"}
              />
            ))}
          </div>
        </div>
      </section>

      {/* ⚙️ 5-STAGE WORKFLOW */}
      <section id="how-it-works" className="py-20 bg-slate-900/60 border-y border-white/10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <span className="text-xs font-extrabold uppercase tracking-widest text-emerald-400">
              Diagnostic Architecture
            </span>
            <h2 className="mt-2 text-3xl font-black text-white">
              The 5-Stage Machine Learning Pipeline
            </h2>
            <p className="mt-3 text-xs sm:text-sm text-slate-400">
              From zero-storage client-side privacy sanitization to Google Gemini multimodal formulation recommendations.
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
                glowColor={index % 2 === 0 ? "emerald" : "cyan"}
              />
            ))}
          </div>
        </div>
      </section>

      {/* 🛡️ SAFETY & CTA */}
      <section className="py-20 bg-slate-950">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 space-y-8">
          <AdBanner />
          <DisclaimerBox />

          {/* 3D Elevated CTA Container */}
          <Card3D glowColor="emerald" className="border-emerald-500/30 bg-gradient-to-r from-slate-950 via-slate-900 to-emerald-950 p-8 sm:p-12 text-center text-white shadow-2xl">
            <div className="pointer-events-none absolute -top-24 left-1/2 -z-0 h-64 w-64 -translate-x-1/2 rounded-full bg-emerald-500/20 blur-3xl" />
            <h2 className="relative z-10 text-3xl font-black sm:text-4xl text-white">
              Ready to Discover Your Personalized Regimen?
            </h2>
            <p className="relative z-10 mx-auto mt-3 max-w-xl text-xs sm:text-sm text-slate-300 leading-relaxed">
              Join thousands of users discovering personalized skincare routines and ingredient hazard analysis in seconds.
            </p>
            <div className="relative z-10 mt-8 flex justify-center">
              <Link
                to={ROUTES.skinProfile}
                className="inline-flex items-center gap-3 rounded-2xl bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 px-8 py-4 text-base font-black text-slate-950 shadow-[0_0_35px_rgba(16,185,129,0.45)] transition-all hover:scale-105 hover:shadow-[0_0_55px_rgba(16,185,129,0.65)]"
              >
                <ScanFace className="h-5 w-5" />
                <span>Start Free Analysis Now</span>
              </Link>
            </div>
          </Card3D>
        </div>
      </section>
    </div>
  );
}


