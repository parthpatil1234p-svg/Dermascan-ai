import { ChevronLeft, ChevronRight, FilterX, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getBrands } from "../services/brandService";
import { getIngredients } from "../services/ingredientService";
import { getCatalogueErrorMessage, getProducts } from "../services/productService";
import {
  CATALOGUE_SKIN_TYPES, FRAGRANCE_STATUSES, PRODUCT_CATEGORIES, SORT_OPTIONS,
  VISIBLE_CONCERNS,
} from "../constants/catalogueOptions";
import ErrorMessage from "./ErrorMessage";
import ProductCard from "./ProductCard";

function SelectFilter({ label, name, value, onChange, options }) {
  return (
    <label className="block text-sm font-semibold text-slate-800">
      {label}
      <select
        name={name} value={value} onChange={(event) => onChange(name, event.target.value)}
        className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 font-normal text-slate-800 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
      >
        <option value="">Any</option>
        {options.map(([optionValue, text]) => <option key={optionValue} value={optionValue}>{text}</option>)}
      </select>
    </label>
  );
}

export default function ProductCatalogue() {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryString = searchParams.toString();
  const [searchDraft, setSearchDraft] = useState(searchParams.get("search") || "");
  const [result, setResult] = useState({ items: [], pagination: null });
  const [brands, setBrands] = useState([]);
  const [ingredients, setIngredients] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const filters = useMemo(
    () => Object.fromEntries(new URLSearchParams(queryString).entries()),
    [queryString],
  );
  const minimum = filters.min_price === undefined ? null : Number(filters.min_price);
  const maximum = filters.max_price === undefined ? null : Number(filters.max_price);
  const invalidPrice = minimum !== null && maximum !== null && maximum < minimum;

  useEffect(() => {
    let active = true;
    Promise.all([getBrands({ page_size: 100 }), getIngredients({ page_size: 100 })])
      .then(([brandData, ingredientData]) => {
        if (active) {
          setBrands(brandData.items);
          setIngredients(ingredientData.items);
        }
      })
      .catch(() => null);
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    if (invalidPrice) {
      setError("Maximum price must be greater than or equal to minimum price.");
      setIsLoading(false);
      return () => { active = false; };
    }
    setIsLoading(true);
    setError("");
    getProducts({ ...filters, page_size: 12 })
      .then((data) => { if (active) setResult(data); })
      .catch((requestError) => { if (active) setError(getCatalogueErrorMessage(requestError)); })
      .finally(() => { if (active) setIsLoading(false); });
    return () => { active = false; };
  }, [filters, invalidPrice]);

  const updateFilter = (name, value) => {
    const next = new URLSearchParams(searchParams);
    value ? next.set(name, value) : next.delete(name);
    next.delete("page");
    setSearchParams(next);
  };

  const submitSearch = (event) => {
    event.preventDefault();
    updateFilter("search", searchDraft.trim());
  };

  const reset = () => {
    setSearchDraft("");
    setSearchParams({});
  };

  const ingredientOptions = ingredients.map((item) => [item.canonical_name.toLowerCase(), item.canonical_name]);
  const brandOptions = brands.map((item) => [item.brand_id, item.brand_name]);
  const page = result.pagination?.page || 1;

  return (
    <div className="mx-auto max-w-7xl">
      <form onSubmit={submitSearch} className="border-y border-slate-200 bg-slate-50 px-4 py-6 sm:px-6" aria-label="Product catalogue filters">
        <div className="flex flex-col gap-3 sm:flex-row">
          <label className="flex-1 text-sm font-semibold text-slate-800">
            Search catalogue
            <span className="mt-2 flex rounded-lg border border-slate-300 bg-white focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-100">
              <Search className="ml-3 mt-3 h-5 w-5 text-slate-400" aria-hidden="true" />
              <input value={searchDraft} onChange={(event) => setSearchDraft(event.target.value)} maxLength={100} placeholder="Product, brand, ingredient, or concern" className="min-w-0 flex-1 bg-transparent px-3 py-2.5 font-normal outline-none" />
            </span>
          </label>
          <button type="submit" className="self-end rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600">Search</button>
          <button type="button" onClick={reset} className="inline-flex items-center justify-center gap-2 self-end rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"><FilterX className="h-4 w-4" aria-hidden="true" /> Reset</button>
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <SelectFilter label="Category" name="category" value={filters.category || ""} onChange={updateFilter} options={PRODUCT_CATEGORIES} />
          <SelectFilter label="Brand" name="brand" value={filters.brand || ""} onChange={updateFilter} options={brandOptions} />
          <SelectFilter label="Skin-type mapping" name="skin_type" value={filters.skin_type || ""} onChange={updateFilter} options={CATALOGUE_SKIN_TYPES} />
          <SelectFilter label="Visible goal mapping" name="visible_concern" value={filters.visible_concern || ""} onChange={updateFilter} options={VISIBLE_CONCERNS} />
          <SelectFilter label="Contains ingredient" name="ingredient" value={filters.ingredient || ""} onChange={updateFilter} options={ingredientOptions} />
          <SelectFilter label="Excludes ingredient" name="exclude_ingredient" value={filters.exclude_ingredient || ""} onChange={updateFilter} options={ingredientOptions} />
          <SelectFilter label="Fragrance status" name="fragrance_status" value={filters.fragrance_status || ""} onChange={updateFilter} options={FRAGRANCE_STATUSES} />
          <SelectFilter label="Availability" name="availability" value={filters.availability || ""} onChange={updateFilter} options={[["available", "Available"], ["limited", "Limited"], ["unavailable", "Unavailable"], ["unknown", "Unknown"]]} />
          <label className="text-sm font-semibold text-slate-800">Minimum price (INR)<input type="number" min="0" max="1000000" step="1" value={filters.min_price || ""} onChange={(event) => updateFilter("min_price", event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5 font-normal focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100" /></label>
          <label className="text-sm font-semibold text-slate-800">Maximum price (INR)<input type="number" min="0" max="1000000" step="1" value={filters.max_price || ""} onChange={(event) => updateFilter("max_price", event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5 font-normal focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100" /></label>
          <SelectFilter label="Country" name="country" value={filters.country || ""} onChange={updateFilter} options={[["IN", "India"]]} />
          <SelectFilter label="Sort" name="sort" value={filters.sort || "name_asc"} onChange={updateFilter} options={SORT_OPTIONS} />
        </div>
      </form>

      <div className="px-4 py-8 sm:px-6">
        {error ? <ErrorMessage message={error} /> : null}
        {isLoading ? (
          <div className="py-16 text-center" role="status"><div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" /><p className="mt-4 text-sm font-semibold text-slate-700">Loading catalogue...</p></div>
        ) : !error && result.items.length === 0 ? (
          <div className="border-y border-slate-200 py-14 text-center"><h2 className="text-xl font-bold text-slate-950">No products match the selected catalogue filters.</h2><p className="mt-2 text-sm text-slate-600">Try increasing the price range or removing one filter. Safety filters are never removed automatically.</p></div>
        ) : !error ? (
          <>
            <div className="mb-5 flex items-center justify-between gap-4"><p className="text-sm font-semibold text-slate-700">{result.pagination.total_items} catalogue result{result.pagination.total_items === 1 ? "" : "s"}</p><p className="text-sm text-slate-500">Page {page} of {result.pagination.total_pages || 1}</p></div>
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">{result.items.map((product) => <ProductCard key={product.product_id} product={product} />)}</div>
            <div className="mt-8 flex justify-center gap-3">
              <button type="button" disabled={!result.pagination.has_previous} onClick={() => updateFilter("page", String(page - 1))} aria-label="Previous catalogue page" className="inline-flex h-11 w-11 items-center justify-center rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"><ChevronLeft className="h-5 w-5" /></button>
              <button type="button" disabled={!result.pagination.has_next} onClick={() => updateFilter("page", String(page + 1))} aria-label="Next catalogue page" className="inline-flex h-11 w-11 items-center justify-center rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"><ChevronRight className="h-5 w-5" /></button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
