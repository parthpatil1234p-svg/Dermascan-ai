import {
  AlertTriangle,
  CheckCircle2,
  FlaskConical,
  Info,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import { useState } from "react";
import PageHeader from "../components/PageHeader";
import { checkIngredients } from "../services/aiService";
import { AdBanner } from "../components/DisclaimerBox";

const SAMPLE_PRODUCTS = [
  {
    name: "10% Niacinamide & Zinc Serum",
    ingredients: "Aqua, Niacinamide (10%), Zinc PCA (1%), Dimethyl Isosorbide, Ethoxydiglycol, Hydroxyethylcellulose, Phenoxyethanol, Ethylhexylglycerin.",
  },
  {
    name: "Salicylic Acid Cleanser",
    ingredients: "Water, Sodium Lauroyl Sarcosinate, Cocamidopropyl Betaine, Salicylic Acid (2%), Glycerin, Niacinamide, Sodium Hyaluronate, Fragrance, EDTA.",
  },
  {
    name: "Heavy Night Cream with Fragrance",
    ingredients: "Aqua, Mineral Oil, Petrolatum, Isopropyl Myristate, Cetyl Alcohol, Lanolin, Stearic Acid, Parfum, Methylparaben, Propylparaben.",
  },
];

export default function IngredientCheckerPage() {
  const [ingredientsText, setIngredientsText] = useState("");
  const [skinType, setSkinType] = useState("all");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    if (!ingredientsText.trim() || loading) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await checkIngredients(ingredientsText.trim(), skinType);
      setResult(data.analysis);
    } catch (err) {
      setError("Failed to analyze ingredients. Please check connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  const loadSample = (sample) => {
    setIngredientsText(sample.ingredients);
    setResult(null);
    setError("");
  };

  return (
    <div className="bg-clinic-50 py-12">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <PageHeader
          eyebrow="AI Ingredient Intelligence"
          title="Skincare Ingredient Safety & Conflict Checker"
          description="Paste any cosmetic formula or product ingredient list to analyze safety scores, pore-clogging risks, potential irritants, and routine layering conflicts powered by Google Gemini AI."
        />

        {/* Input Card */}
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <form onSubmit={handleAnalyze} className="space-y-6">
            <div>
              <div className="flex items-center justify-between">
                <label htmlFor="ingredients-input" className="block text-sm font-bold text-slate-900">
                  Enter Ingredient List (INCI formula)
                </label>
                <span className="text-xs text-slate-500">Comma-separated format</span>
              </div>
              <textarea
                id="ingredients-input"
                rows={4}
                value={ingredientsText}
                onChange={(e) => setIngredientsText(e.target.value)}
                placeholder="e.g. Aqua, Niacinamide, Glycerin, Salicylic Acid, Phenoxyethanol, Parfum..."
                className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-200"
              />
            </div>

            {/* Quick Samples */}
            <div>
              <p className="text-xs font-semibold text-slate-500 mb-2">Try a sample formula:</p>
              <div className="flex flex-wrap gap-2">
                {SAMPLE_PRODUCTS.map((sample) => (
                  <button
                    key={sample.name}
                    type="button"
                    onClick={() => loadSample(sample)}
                    className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:border-brand-300 hover:bg-brand-50 hover:text-brand-800 transition"
                  >
                    ✨ {sample.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="skin-type-select" className="block text-sm font-semibold text-slate-700">
                  Target Skin Type
                </label>
                <select
                  id="skin-type-select"
                  value={skinType}
                  onChange={(e) => setSkinType(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-900 focus:border-brand-600 focus:bg-white focus:outline-none"
                >
                  <option value="all">General / All Skin Types</option>
                  <option value="oily">Oily Skin</option>
                  <option value="dry">Dry Skin</option>
                  <option value="combination">Combination Skin</option>
                  <option value="sensitive">Sensitive Skin</option>
                </select>
              </div>

              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={!ingredientsText.trim() || loading}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-700 to-teal-600 px-6 py-3 text-sm font-semibold text-white shadow-md transition hover:from-brand-800 hover:to-teal-700 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Analyzing Ingredients with Gemini...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-5 w-5 text-amber-300" />
                      Run AI Safety Analysis
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>

          {error && (
            <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 shrink-0 text-red-600" />
              <span>{error}</span>
            </div>
          )}
        </section>

        {/* Ad Placement */}
        <AdBanner className="my-8" />

        {/* Results Section */}
        {result && (
          <section className="mt-8 space-y-6 animate-in fade-in zoom-in-95 duration-300">
            {/* Overview Card */}
            <div className="grid gap-6 sm:grid-cols-3">
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm text-center">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Overall Rating</p>
                <div className="mt-2 flex items-center justify-center gap-2">
                  <span
                    className={`inline-flex rounded-full px-4 py-1 text-base font-bold ${
                      result.overall_rating === "Good"
                        ? "bg-emerald-100 text-emerald-800"
                        : result.overall_rating === "Moderate"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-red-100 text-red-800"
                    }`}
                  >
                    {result.overall_rating}
                  </span>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm text-center">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Safety Score</p>
                <p className="mt-2 text-3xl font-extrabold text-brand-700">{result.safety_score} / 100</p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col justify-center">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Formulation Summary</p>
                <p className="mt-1 text-xs sm:text-sm text-slate-700 leading-relaxed">{result.summary}</p>
              </div>
            </div>

            {/* Beneficial vs Irritants */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Key Beneficial Ingredients */}
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-6">
                <div className="flex items-center gap-2.5 text-emerald-900 font-bold mb-4">
                  <ShieldCheck className="h-5 w-5 text-emerald-600" />
                  <h3>Key Beneficial Ingredients</h3>
                </div>
                {result.key_beneficial_ingredients?.length ? (
                  <ul className="space-y-3">
                    {result.key_beneficial_ingredients.map((item, idx) => (
                      <li key={idx} className="rounded-xl bg-white p-3 border border-emerald-100 shadow-xs">
                        <p className="font-semibold text-sm text-slate-900">{item.name}</p>
                        <p className="text-xs text-slate-600 mt-0.5">{item.benefit}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">No major highlighted active agents found.</p>
                )}
              </div>

              {/* Potential Irritants / Comedogenic */}
              <div className="rounded-2xl border border-amber-200 bg-amber-50/50 p-6">
                <div className="flex items-center gap-2.5 text-amber-900 font-bold mb-4">
                  <ShieldAlert className="h-5 w-5 text-amber-600" />
                  <h3>Irritant & Sensitivity Watchlist</h3>
                </div>
                {result.potential_irritants_or_comedogenic?.length ? (
                  <ul className="space-y-3">
                    {result.potential_irritants_or_comedogenic.map((item, idx) => (
                      <li key={idx} className="rounded-xl bg-white p-3 border border-amber-100 shadow-xs">
                        <p className="font-semibold text-sm text-slate-900">{item.name}</p>
                        <p className="text-xs text-amber-800 mt-0.5">{item.concern}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="flex items-center gap-2 text-sm text-emerald-700 bg-white p-3 rounded-xl border border-emerald-100">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>No harsh irritants or pore-clogging triggers detected!</span>
                  </div>
                )}
              </div>
            </div>

            {/* Layering & Conflicts Card */}
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2 font-bold text-slate-900 mb-3">
                <Zap className="h-5 w-5 text-amber-500" />
                <h3>Application & Layering Advice</h3>
              </div>
              <p className="text-sm text-slate-700 leading-relaxed">{result.layering_advice}</p>

              {result.conflicts_to_avoid?.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-100">
                  <p className="text-xs font-bold text-red-700 uppercase tracking-wide mb-2">
                    ⚠️ Ingredient Conflicts To Avoid:
                  </p>
                  <ul className="list-disc list-inside text-xs sm:text-sm text-slate-700 space-y-1">
                    {result.conflicts_to_avoid.map((conflict, idx) => (
                      <li key={idx}>{conflict}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
