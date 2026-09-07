import {
  AlertTriangle,
  CheckCircle2,
  Cpu,
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
import Card3D from "../components/Card3D";
import BiometricGauge3D from "../components/BiometricGauge3D";

const SAMPLE_PRODUCTS = [
  {
    name: "10% Niacinamide & Zinc Serum",
    ingredients: "Aqua, Niacinamide (10%), Zinc PCA (1%), Dimethyl Isosorbide, Ethoxydiglycol, Hydroxyethylcellulose, Phenoxyethanol, Ethylhexylglycerin.",
  },
  {
    name: "Salicylic Acid 2% Exfoliant",
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
    <div className="relative min-h-screen bg-slate-950 py-12 text-slate-100">
      <div className="relative mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <PageHeader
          eyebrow="Molecular Safety & Layering Intelligence"
          title="AI Ingredient Safety & Hazard Analyzer"
          description="Paste any cosmetic formula or INCI ingredient list to evaluate comedogenic pore-clogging risks, fragrance allergens, and routine layering conflicts powered by Google Gemini AI."
        />

        {/* Input Card */}
        <Card3D glowColor="emerald" className="border-white/10 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-2xl">
          <form onSubmit={handleAnalyze} className="space-y-6">
            <div>
              <div className="flex items-center justify-between">
                <label htmlFor="ingredients-input" className="flex items-center gap-2 text-sm font-bold text-white">
                  <FlaskConical className="h-4 w-4 text-emerald-400" />
                  INCI Cosmetic Formulation
                </label>
                <span className="text-[11px] font-semibold text-slate-400">Comma-separated format</span>
              </div>
              <textarea
                id="ingredients-input"
                rows={4}
                value={ingredientsText}
                onChange={(e) => setIngredientsText(e.target.value)}
                placeholder="e.g. Aqua, Niacinamide (10%), Glycerin, Salicylic Acid, Phenoxyethanol, Parfum..."
                className="mt-2.5 w-full rounded-2xl border border-white/10 bg-slate-950/80 p-4 text-sm text-white placeholder:text-slate-500 focus:border-emerald-500 focus:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              />
            </div>

            {/* Quick Samples */}
            <div>
              <p className="text-xs font-semibold text-slate-400 mb-2.5">Try a verified formulation preset:</p>
              <div className="flex flex-wrap gap-2">
                {SAMPLE_PRODUCTS.map((sample) => (
                  <button
                    key={sample.name}
                    type="button"
                    onClick={() => loadSample(sample)}
                    className="rounded-xl border border-white/10 bg-slate-800/80 px-3.5 py-1.5 text-xs font-semibold text-slate-200 hover:border-emerald-500/40 hover:bg-slate-800 hover:text-emerald-300 transition"
                  >
                    🧪 {sample.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 sm:items-end">
              <div>
                <label htmlFor="skin-type-select" className="block text-xs font-bold uppercase tracking-wider text-slate-400">
                  Target Skin Type
                </label>
                <select
                  id="skin-type-select"
                  value={skinType}
                  onChange={(e) => setSkinType(e.target.value)}
                  className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950/80 px-4 py-3 text-sm text-white focus:border-emerald-500 focus:outline-none"
                >
                  <option value="all">Universal / All Skin Types</option>
                  <option value="oily">Oily & Acne-Prone Skin</option>
                  <option value="dry">Dry & Dehydrated Skin</option>
                  <option value="combination">Combination Skin</option>
                  <option value="sensitive">Sensitive / Irritable Skin</option>
                </select>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={!ingredientsText.trim() || loading}
                  className="inline-flex w-full items-center justify-center gap-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 px-6 py-3 text-sm font-black text-slate-950 shadow-lg shadow-emerald-500/25 transition-all hover:scale-105 hover:shadow-emerald-500/40 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Analyzing Chemical Profiles...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-5 w-5" />
                      Execute Safety Audit
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>

          {error && (
            <div className="mt-6 rounded-xl border border-rose-500/30 bg-rose-950/40 p-4 text-sm text-rose-300 flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}
        </Card3D>

        {/* Ad Placement */}
        <AdBanner className="my-8" />

        {/* Results Section */}
        {result && (
          <section className="mt-8 space-y-6 animate-in fade-in zoom-in-95 duration-300">
            {/* 3D Overview Card with Biometric Gauge */}
            <Card3D glowColor="emerald" className="border-white/10 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-2xl">
              <div className="grid gap-6 md:grid-cols-[0.8fr_1.2fr] md:items-center">
                <div className="flex flex-col items-center justify-center border-b border-slate-800 pb-6 md:border-b-0 md:border-r md:pr-6 md:pb-0">
                  <BiometricGauge3D
                    score={result.safety_score || 85}
                    label={`Safety: ${result.overall_rating}`}
                    grade={result.overall_rating}
                    color={result.overall_rating === "Good" ? "emerald" : result.overall_rating === "Moderate" ? "amber" : "rose"}
                    size={160}
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-bold text-emerald-400 border border-emerald-500/20">
                      Formulation Assessment
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-white">Clinical Summary</h3>
                  <p className="text-xs sm:text-sm leading-relaxed text-slate-300">
                    {result.summary}
                  </p>
                </div>
              </div>
            </Card3D>

            {/* Beneficial vs Irritants */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Key Beneficial Ingredients */}
              <Card3D glowColor="emerald" className="border-emerald-500/20 bg-slate-900/80 p-6 backdrop-blur-xl">
                <div className="flex items-center gap-2.5 text-emerald-400 font-bold mb-4">
                  <ShieldCheck className="h-5 w-5" />
                  <h3 className="text-base text-white font-bold">Key Beneficial Actives</h3>
                </div>
                {result.key_beneficial_ingredients?.length ? (
                  <ul className="space-y-2.5">
                    {result.key_beneficial_ingredients.map((item, idx) => (
                      <li key={idx} className="rounded-xl bg-slate-950/80 p-3.5 border border-white/5 shadow-xs">
                        <p className="font-bold text-sm text-emerald-300">{item.name}</p>
                        <p className="text-xs text-slate-300 mt-1">{item.benefit}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-400">No major concentrated active compounds detected.</p>
                )}
              </Card3D>

              {/* Potential Irritants / Comedogenic */}
              <Card3D glowColor="violet" className="border-amber-500/20 bg-slate-900/80 p-6 backdrop-blur-xl">
                <div className="flex items-center gap-2.5 text-amber-400 font-bold mb-4">
                  <ShieldAlert className="h-5 w-5" />
                  <h3 className="text-base text-white font-bold">Irritant & Sensitivity Watchlist</h3>
                </div>
                {result.potential_irritants_or_comedogenic?.length ? (
                  <ul className="space-y-2.5">
                    {result.potential_irritants_or_comedogenic.map((item, idx) => (
                      <li key={idx} className="rounded-xl bg-slate-950/80 p-3.5 border border-white/5 shadow-xs">
                        <p className="font-bold text-sm text-amber-300">{item.name}</p>
                        <p className="text-xs text-slate-300 mt-1">{item.concern}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 bg-emerald-950/30 p-4 rounded-xl border border-emerald-500/20">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>No severe comedogenic triggers or harsh fragrance allergens identified!</span>
                  </div>
                )}
              </Card3D>
            </div>

            {/* Layering & Conflicts Card */}
            <Card3D glowColor="cyan" className="border-white/10 bg-slate-900/80 p-6 sm:p-7 backdrop-blur-xl">
              <div className="flex items-center gap-2 font-bold text-white mb-3">
                <Zap className="h-5 w-5 text-cyan-400" />
                <h3 className="text-base font-bold">Application & Layering Protocol</h3>
              </div>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">{result.layering_advice}</p>

              {result.conflicts_to_avoid?.length > 0 && (
                <div className="mt-5 pt-4 border-t border-slate-800">
                  <p className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                    <AlertTriangle className="h-4 w-4" />
                    Ingredient Conflicts To Avoid In Same Routine:
                  </p>
                  <ul className="grid gap-2 sm:grid-cols-2 text-xs text-slate-300">
                    {result.conflicts_to_avoid.map((conflict, idx) => (
                      <li key={idx} className="rounded-lg bg-rose-950/30 border border-rose-500/20 p-2.5">
                        ⚠️ {conflict}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Card3D>
          </section>
        )}
      </div>
    </div>
  );
}

