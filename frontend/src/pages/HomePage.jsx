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
import DisclaimerBox from "../components/DisclaimerBox";
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
    <div className="bg-clinic-50">
      <section className="bg-white">
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[1fr_0.92fr] lg:px-8 lg:py-20">
          <div>
            <p className="inline-flex rounded-full bg-brand-50 px-4 py-2 text-sm font-semibold text-brand-700">
              DermaScan AI college mini-project
            </p>
            <h1 className="mt-6 max-w-3xl text-4xl font-bold leading-tight text-slate-950 sm:text-5xl">
              Understand Your Skin with AI-Powered Analysis
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              Upload or capture a clear facial image to receive an AI-assisted
              skin-type analysis, visible skin observations, personalized
              product recommendations, and a simple skincare routine.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <PrimaryButton to={ROUTES.skinProfile} icon={ScanFace}>
                Start Skin Analysis
              </PrimaryButton>
              <SecondaryButton to="/#how-it-works" icon={ArrowRight}>
                Learn How It Works
              </SecondaryButton>
            </div>
          </div>

          <div className="relative">
            <img
              src={heroImage}
              alt="AI-assisted skin analysis interface showing a facial scan and skincare data panels"
              className="aspect-[4/3] w-full rounded-lg border border-slate-200 object-cover shadow-soft"
            />
            <div className="absolute bottom-4 left-4 right-4 rounded-lg border border-white/60 bg-white/90 p-4 shadow-sm backdrop-blur">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-leaf-100 text-leaf-700">
                  <Leaf aria-hidden="true" className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-sm font-semibold text-slate-950">
                    Guidance only, not diagnosis
                  </p>
                  <p className="text-sm text-slate-600">
                    Designed for safe skincare education and demonstrations.
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
