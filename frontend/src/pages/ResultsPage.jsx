import { AlertTriangle, FlaskConical, Moon, ShieldCheck, Sun } from "lucide-react";
import DisclaimerBox from "../components/DisclaimerBox";
import PageHeader from "../components/PageHeader";
import ProductCard from "../components/ProductCard";
import ResultCard from "../components/ResultCard";
import RoutineCard from "../components/RoutineCard";
import SecondaryButton from "../components/SecondaryButton";
import { ROUTES } from "../constants/appContent";
import { useDemoData } from "../context/DemoDataContext";

export default function ResultsPage() {
  const { demoResults } = useDemoData();

  return (
    <section className="px-4 py-14 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="Demonstration results"
        title="Static sample skin guidance report"
        description="The information shown here is demonstration data only. It is not generated from a real uploaded image and must not be treated as a medical result."
      />

      <div className="mx-auto max-w-7xl space-y-8">
        <div className="rounded-lg border border-brand-200 bg-brand-50 p-5 text-brand-900">
          <div className="flex items-start gap-3">
            <AlertTriangle
              aria-hidden="true"
              className="mt-0.5 h-5 w-5 shrink-0"
            />
            <p className="text-sm leading-6">
              Demo data notice: these values are static placeholders for the current
              and do not represent a genuine scan, diagnosis, or final
              recommendation algorithm.
            </p>
          </div>
        </div>

        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          <ResultCard
            title="Likely skin type"
            value={demoResults.skinType}
            helper="Sample value for interface demonstration"
          />
          <ResultCard
            title="AI confidence score"
            value={`${demoResults.confidence}%`}
            helper="Static score, not produced by a real model"
          />
          <ResultCard
            title="Safety label"
            value="Guidance only"
            helper="Not a medical diagnosis"
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
          <ResultCard title="Visible skin observations">
            <ul className="space-y-3">
              {demoResults.observations.map((observation) => (
                <li key={observation} className="flex gap-3 text-sm text-slate-700">
                  <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-brand-600" />
                  <span>{observation}</span>
                </li>
              ))}
            </ul>
          </ResultCard>

          <ResultCard title="Safety instructions">
            <ul className="space-y-3 text-sm leading-6 text-slate-700">
              <li className="flex gap-3">
                <ShieldCheck
                  aria-hidden="true"
                  className="mt-0.5 h-5 w-5 shrink-0 text-leaf-700"
                />
                Use results only as general skincare guidance.
              </li>
              <li className="flex gap-3">
                <ShieldCheck
                  aria-hidden="true"
                  className="mt-0.5 h-5 w-5 shrink-0 text-leaf-700"
                />
                Do a patch test before trying new products.
              </li>
              <li className="flex gap-3">
                <ShieldCheck
                  aria-hidden="true"
                  className="mt-0.5 h-5 w-5 shrink-0 text-leaf-700"
                />
                Consult a dermatologist for severe or persistent concerns.
              </li>
            </ul>
          </ResultCard>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <ResultCard title="Recommended ingredients">
            <ul className="grid gap-3 sm:grid-cols-2">
              {demoResults.recommendedIngredients.map((ingredient) => (
                <li
                  key={ingredient}
                  className="flex items-center gap-3 rounded-lg bg-leaf-50 px-3 py-3 text-sm font-medium text-leaf-700"
                >
                  <FlaskConical aria-hidden="true" className="h-4 w-4" />
                  {ingredient}
                </li>
              ))}
            </ul>
          </ResultCard>
          <ResultCard title="Ingredients to avoid">
            <ul className="grid gap-3">
              {demoResults.ingredientsToAvoid.map((ingredient) => (
                <li
                  key={ingredient}
                  className="flex items-center gap-3 rounded-lg bg-amber-50 px-3 py-3 text-sm font-medium text-amber-800"
                >
                  <AlertTriangle aria-hidden="true" className="h-4 w-4" />
                  {ingredient}
                </li>
              ))}
            </ul>
          </ResultCard>
        </div>

        <section>
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-brand-700">
                Demo product suggestions
              </p>
              <h2 className="mt-2 text-2xl font-bold text-slate-950">
                Product recommendation cards
              </h2>
            </div>
            <SecondaryButton to={ROUTES.reports}>View Previous Reports</SecondaryButton>
          </div>
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {demoResults.products.map((product) => (
              <ProductCard key={product.name} product={product} />
            ))}
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <RoutineCard
            icon={Sun}
            title="Morning skincare routine"
            steps={demoResults.morningRoutine}
          />
          <RoutineCard
            icon={Moon}
            title="Night skincare routine"
            steps={demoResults.nightRoutine}
          />
        </section>

        <DisclaimerBox />
      </div>
    </section>
  );
}
