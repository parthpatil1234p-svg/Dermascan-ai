import { ArrowLeft, FlaskConical } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import { displayCode } from "../constants/catalogueOptions";
import { getIngredientById } from "../services/ingredientService";

export default function IngredientDetailPage() {
  const { ingredientId } = useParams();
  const [ingredient, setIngredient] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    getIngredientById(ingredientId).then((data) => { if (active) setIngredient(data); }).catch(() => { if (active) setError("Ingredient information could not be loaded."); });
    return () => { active = false; };
  }, [ingredientId]);
  if (error) return <section className="mx-auto max-w-3xl px-4 py-16"><ErrorMessage message={error} /></section>;
  if (!ingredient) return <p className="py-24 text-center text-sm font-semibold text-slate-600" role="status">Loading ingredient record...</p>;
  return (
    <section className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <Link to="/ingredients" className="inline-flex items-center gap-2 text-sm font-semibold text-brand-700"><ArrowLeft className="h-4 w-4" /> Ingredient directory</Link>
      <header className="mt-7 border-b border-slate-200 pb-8"><span className="flex h-11 w-11 items-center justify-center rounded-lg bg-clinic-50 text-clinic-700"><FlaskConical className="h-6 w-6" /></span><p className="mt-5 text-sm font-bold uppercase tracking-wide text-brand-700">{displayCode(ingredient.ingredient_category)}</p><h1 className="mt-2 text-3xl font-bold text-slate-950">{ingredient.canonical_name}</h1><p className="mt-3 text-slate-600">Aliases: {ingredient.aliases.join(", ") || "None recorded"}</p></header>
      <div className="grid gap-8 py-8 md:grid-cols-2"><section><h2 className="text-xl font-bold text-slate-950">General skincare roles</h2><ul className="mt-4 space-y-2 text-sm leading-6 text-slate-700">{ingredient.common_skincare_roles.map((item) => <li key={item} className="border-b border-slate-200 py-2">{item}</li>)}</ul></section><section><h2 className="text-xl font-bold text-slate-950">Caution notes</h2><ul className="mt-4 space-y-2 text-sm leading-6 text-slate-700">{ingredient.caution_notes.length ? ingredient.caution_notes.map((item) => <li key={item} className="border-b border-slate-200 py-2">{item}</li>) : <li>No specific catalogue caution note is recorded. Individual tolerance can still vary.</li>}</ul></section></div>
      <section className="border-t border-slate-200 pt-8"><h2 className="text-xl font-bold text-slate-950">Catalogue products containing this ingredient</h2><div className="mt-4 grid gap-3 sm:grid-cols-2">{ingredient.products.length ? ingredient.products.map((product) => <Link key={product.product_id} to={`/products/${product.product_id}`} className="rounded-lg border border-slate-200 p-4 hover:border-brand-300 hover:bg-brand-50"><span className="font-semibold text-slate-950">{product.product_name}</span><span className="mt-1 block text-sm text-slate-600">{product.brand_name} - {displayCode(product.category)}</span>{product.is_demo_product ? <span className="mt-2 inline-block text-xs font-bold text-amber-800">Demonstration Product</span> : null}</Link>) : <p className="text-sm text-slate-600">No active public catalogue products currently reference this ingredient.</p>}</div></section>
      <p className="mt-8 border-y border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-950">{ingredient.disclaimer}</p>
    </section>
  );
}

