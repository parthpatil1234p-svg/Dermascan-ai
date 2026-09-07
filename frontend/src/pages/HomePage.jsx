import {
  ArrowRight,
  BrainCircuit,
  ClipboardList,
  FlaskConical,
  Leaf,
  ListChecks,
  ScanFace,
  Search,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  Wallet,
} from "lucide-react";
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
  Wallet,
  FlaskConical,
  ListChecks,
];

export default function HomePage() {
  return (
    <div className="bg-slate-50/50">
      {/* Modern Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-white via-brand-50/30 to-slate-50 py-16 sm:py-24">
        {/* Subtle decorative background blur shapes */}
        <div className="pointer-events-none absolute -top-24 left-1/2 -z-10 h-96 w-96 -translate-x-1/2 rounded-full bg-teal-200/30 blur-3xl" />
        <div className="pointer-events-none absolute top-1/3 -right-24 -z-10 h-72 w-72 rounded-full bg-brand-200/20 blur-2xl" />

        <div className="mx-auto grid max-w-7xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-teal-200 bg-white/80 px-3.5 py-1.5 text-xs font-bold text-teal-800 shadow-xs backdrop-blur-sm">
              <Sparkles className="h-3.5 w-3.5 text-amber-500 animate-pulse" />
              <span>Google Gemini AI Vision Powered</span>
            </div>

            <h1 className="mt-6 max-w-2xl text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
              Understand Your Skin with{" "}
              <span className="gradient-text">AI-Powered Analysis</span>
            </h1>

            <p className="mt-6 max-w-xl text-base sm:text-lg leading-relaxed text-slate-600">
              Upload or capture a clear facial image to receive real-time AI-assisted
              skin-type analysis, visible skin observations, personalized
              product recommendations, and a customized routine.
            </p>

            <div className="mt-8 flex flex-col gap-3.5 sm:flex-row">
              <PrimaryButton to={ROUTES.skinProfile} icon={ScanFace} className="shadow-lg shadow-brand-700/20">
                Start Free Skin Analysis
              </PrimaryButton>
              <SecondaryButton to={ROUTES.ingredientChecker} icon={FlaskConical}>
                AI Ingredient Checker
              </SecondaryButton>
            </div>

            {/* Quick feature highlights */}
            <div className="mt-10 grid grid-cols-3 gap-4 border-t border-slate-200/80 pt-6 text-center sm:text-left">
              <div>
                <p className="text-xl sm:text-2xl font-black text-brand-700">100%</p>
                <p className="text-xs text-slate-500 mt-0.5">Free & Instant</p>
              </div>
              <div>
                <p className="text-xl sm:text-2xl font-black text-brand-700">AI 24/7</p>
                <p className="text-xs text-slate-500 mt-0.5">Gemini Vision</p>
              </div>
              <div>
                <p className="text-xl sm:text-2xl font-black text-brand-700">Private</p>
                <p className="text-xs text-slate-500 mt-0.5">Secure Storage</p>
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-2 shadow-xl shadow-slate-900/5">
              <img
                src={heroImage}
                alt="AI-assisted skin analysis interface showing a facial scan and skincare data panels"
                className="aspect-[4/3] w-full rounded-xl object-cover"
              />
            </div>

            {/* Floating Glassmorphic Badge */}
            <div className="absolute -bottom-5 left-4 right-4 rounded-xl border border-white/80 bg-white/90 p-4 shadow-lg backdrop-blur-md transition-transform hover:scale-[1.02] sm:left-6 sm:right-6">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-leaf-100 text-leaf-700 shadow-xs">
                  <Leaf aria-hidden="true" className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-xs sm:text-sm font-bold text-slate-900">
                    Safe Skincare Guidance
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Designed for smart skincare decision support and education.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="how-it-works" className="py-16 sm:py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-wide text-brand-700">
              How it works
            </p>
            <h2 className="mt-3 text-3xl font-bold text-slate-950">
              A responsible workflow for AI-assisted skincare guidance
            </h2>
            <p className="mt-4 text-base leading-7 text-slate-600">
              Accounts, profiles, private image preparation, broad skin-type
              estimation, and cautious visible-concern reporting are connected.
              Model stages run only with validated artifacts; product guidance
              remains planned.
            </p>
          </div>
          <div className="mt-10 grid gap-5 md:grid-cols-2 lg:grid-cols-5">
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

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <AdBanner />
      </div>

      <section id="benefits" className="bg-white py-16 sm:py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-wide text-brand-700">
              Benefits
            </p>
            <h2 className="mt-3 text-3xl font-bold text-slate-950">
              Designed for practical skincare decision support
            </h2>
          </div>
          <div className="mt-10 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {BENEFITS.map((benefit, index) => (
              <BenefitCard
                key={benefit.title}
                icon={benefitIcons[index]}
                title={benefit.title}
                description={benefit.description}
              />
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 sm:py-20">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-brand-700">
              Safety first
            </p>
            <h2 className="mt-3 text-3xl font-bold text-slate-950">
              Clear limits keep the project responsible
            </h2>
            <p className="mt-4 text-base leading-7 text-slate-600">
              DermaScan AI should support skincare awareness, not replace
              professional medical advice. Its output must always be framed as
              guidance based on visible characteristics and user-provided
              details.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <FeatureCard
              icon={ShieldCheck}
              title="General guidance only"
              description="The system must not diagnose diseases, prescribe treatment, or claim medical certainty."
            />
            <FeatureCard
              icon={UploadCloud}
              title="Image quality matters"
              description="Lighting, shadows, makeup, angle, and blur can affect future analysis quality."
            />
            <FeatureCard
              icon={BrainCircuit}
              title="Transparent demo status"
              description="Quality, face, and model stages expose real readiness and uncertainty. No result is replaced with invented demo output."
            />
            <FeatureCard
              icon={ShieldCheck}
              title="Dermatologist advice"
              description="Severe, painful, changing, or persistent skin concerns require a qualified dermatologist."
            />
          </div>
        </div>
      </section>

      <section className="bg-white py-16 sm:py-20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <AdBanner className="mb-8" />
          <DisclaimerBox />
          <div className="mt-8 rounded-lg border border-slate-200 bg-clinic-50 p-8 text-center shadow-sm">
            <h2 className="text-2xl font-bold text-slate-950">
              Ready to complete your skin profile?
            </h2>
            <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-slate-600">
              Start with the skin profile questionnaire, then continue to image
              upload and a real technical quality report.
            </p>
            <PrimaryButton to={ROUTES.skinProfile} className="mt-6" icon={ScanFace}>
              Start Analysis
            </PrimaryButton>
          </div>
        </div>
      </section>
    </div>
  );
}
