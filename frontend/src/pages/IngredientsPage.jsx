import { Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import PageHeader from "../components/PageHeader";
import { displayCode } from "../constants/catalogueOptions";
import { getIngredients } from "../services/ingredientService";

const categories = ["active", "humectant", "emollient", "occlusive", "surfactant", "antioxidant", "preservative", "fragrance", "essential_oil", "exfoliant", "uv_filter", "soothing_agent", "colourant", "solvent", "other"];

export default function IngredientsPage() {
  const [params, setParams] = useSearchParams();
  const queryString = params.toString();
  const filters = useMemo(
    () => Object.fromEntries(new URLSearchParams(queryString).entries()),
    [queryString],
  );
  const [search, setSearch] = useState(params.get("search") || "");
  const [data, setData] = useState({ items: [], pagination: null });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    getIngredients(filters)
      .then((result) => { if (active) setData(result); })
      .catch(() => { if (active) setError("Ingredient information could not be loaded."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [filters]);

  const update = (name, value) => {
    const next = new URLSearchParams(params);
    value ? next.set(name, value) : next.delete(name);
    next.delete("page");
    setParams(next);
  };

  return (
    <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
      <PageHeader eyebrow="Controlled ingredient taxonomy" title="Skincare Ingredient Directory" description="Review canonical names, known aliases, general cosmetic roles, and cautious notes. This directory does not provide dosing or medical treatment advice." />
      <form onSubmit={(event) => { event.preventDefault(); update("search", search.trim()); }} className="grid gap-4 border-y border-slate-200 bg-slate-50 p-5 sm:grid-cols-[1fr_220px_auto]">
        <label className="text-sm font-semibold text-slate-800">Search ingredients<span className="mt-2 flex rounded-lg border border-slate-300 bg-white"><Search className="ml-3 mt-3 h-5 w-5 text-slate-400" /><input value={search} onChange={(event) => setSearch(event.target.value)} maxLength={100} className="min-w-0 flex-1 bg-transparent px-3 py-2.5 font-normal outline-none" placeholder="Name or alias" /></span></label>
        <label className="text-sm font-semibold text-slate-800">Category<select value={params.get("ingredient_category") || ""} onChange={(event) => update("ingredient_category", event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 font-normal"><option value="">Any</option>{categories.map((category) => <option key={category} value={category}>{displayCode(category)}</option>)}</select></label>
        <button className="self-end rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">Search</button>
      </form>
      {error ? <ErrorMessage message={error} /> : null}
      {loading ? <p className="py-14 text-center text-sm font-semibold text-slate-600" role="status">Loading ingredient directory...</p> : (
        <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">{data.items.map((ingredient) => <article key={ingredient.ingredient_id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"><p className="text-xs font-bold uppercase tracking-wide text-brand-700">{displayCode(ingredient.ingredient_category)}</p><h2 className="mt-2 text-lg font-bold text-slate-950">{ingredient.canonical_name}</h2><p className="mt-2 text-sm text-slate-600">{ingredient.aliases.length ? `Also known as ${ingredient.aliases.join(", ")}` : "No aliases recorded"}</p><p className="mt-4 text-sm leading-6 text-slate-600">{ingredient.common_skincare_roles.join(", ") || "No general roles recorded."}</p><Link to={`/ingredients/${ingredient.ingredient_id}`} className="mt-5 inline-flex font-semibold text-brand-700 hover:text-brand-800">View ingredient details</Link></article>)}</div>
      )}
      {!loading && !error && !data.items.length ? <p className="border-y border-slate-200 py-12 text-center text-slate-600">No ingredients match this search.</p> : null}
    </section>
  );
}
