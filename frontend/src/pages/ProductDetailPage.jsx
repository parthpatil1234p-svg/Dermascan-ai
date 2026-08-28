import { ArrowLeft, CalendarClock, ExternalLink, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import DisclaimerBox from "../components/DisclaimerBox";
import ErrorMessage from "../components/ErrorMessage";
import { displayCode } from "../constants/catalogueOptions";
import { getCatalogueErrorMessage, getProductById } from "../services/productService";

function formatDate(value) {
  return value ? new Intl.DateTimeFormat("en-IN", { dateStyle: "long" }).format(new Date(value)) : "Not recorded";
}

function Tags({ values }) {
  return <div className="mt-2 flex flex-wrap gap-2">{values.length ? values.map((value) => <span key={value} className="rounded-full bg-clinic-50 px-3 py-1 text-xs font-semibold text-clinic-800">{displayCode(value)}</span>) : <span className="text-sm text-slate-500">None recorded</span>}</div>;
}

export default function ProductDetailPage() {
  const { productId } = useParams();
  const [product, setProduct] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    getProductById(productId)
      .then((data) => { if (active) setProduct(data); })
      .catch((requestError) => { if (active) setError(getCatalogueErrorMessage(requestError)); });
    return () => { active = false; };
  }, [productId]);

  if (error) return <section className="mx-auto max-w-3xl px-4 py-16"><ErrorMessage message={error} /><Link to="/products" className="mt-6 inline-flex items-center gap-2 font-semibold text-brand-700"><ArrowLeft className="h-4 w-4" /> Back to catalogue</Link></section>;
  if (!product) return <div className="py-24 text-center" role="status"><div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" /><p className="mt-4 text-sm font-semibold text-slate-700">Loading product record...</p></div>;

  return (
    <section className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <Link to="/products" className="inline-flex items-center gap-2 text-sm font-semibold text-brand-700 hover:text-brand-800"><ArrowLeft className="h-4 w-4" /> Back to catalogue</Link>
      <header className="mt-6 border-b border-slate-200 pb-8">
        <div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-bold text-brand-800">{product.category_display}</span>{product.is_demo_product ? <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-900">Demonstration Product</span> : <span className="rounded-full bg-leaf-100 px-3 py-1 text-xs font-bold text-leaf-800">{displayCode(product.data_type)}</span>}</div>
        <p className="mt-5 text-sm font-semibold text-brand-700">{product.brand_name}</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-950 sm:text-4xl">{product.product_name}</h1>
        <p className="mt-4 max-w-3xl leading-7 text-slate-600">{product.short_description}</p>
        {product.demo_label ? <p className="mt-4 font-semibold text-amber-900">{product.demo_label}</p> : null}
      </header>

      <div className="grid gap-10 py-8 lg:grid-cols-[1.25fr_0.75fr]">
        <div className="space-y-8">
          <section><h2 className="text-xl font-bold text-slate-950">Catalogue mappings</h2><h3 className="mt-4 text-sm font-bold text-slate-800">Suitable skin-type metadata</h3><Tags values={product.suitable_skin_types} /><h3 className="mt-5 text-sm font-bold text-slate-800">Visible skincare goals</h3><Tags values={product.target_visible_concerns} /></section>
          <section><h2 className="text-xl font-bold text-slate-950">Ingredients</h2><p className="mt-2 text-sm leading-6 text-slate-600">Ingredient order follows the available source record and does not reveal exact concentration.</p><ol className="mt-4 grid gap-2 sm:grid-cols-2">{product.ingredients.map((item) => <li key={`${item.position}-${item.display_name}`} className="border-b border-slate-200 py-2 text-sm text-slate-700"><span className="mr-2 font-semibold text-slate-500">{item.position}.</span>{item.display_name}</li>)}</ol><h3 className="mt-6 text-sm font-bold text-slate-800">General caution flags</h3><Tags values={product.potential_irritant_flags} /></section>
          <section className="border-y border-amber-200 bg-amber-50 px-5 py-5"><h2 className="flex items-center gap-2 font-bold text-amber-950"><ShieldAlert className="h-5 w-5" aria-hidden="true" /> General safety note</h2><p className="mt-2 text-sm leading-6 text-amber-950">Product information may change. Always review the current packaging and official manufacturer information before use.</p><p className="mt-2 text-sm leading-6 text-amber-950">Perform a patch test when introducing a new product, especially if you report skin sensitivity or known allergies.</p></section>
        </div>

        <aside className="space-y-6">
          <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"><h2 className="font-bold text-slate-950">Catalogue snapshot</h2><dl className="mt-4 space-y-4 text-sm"><div><dt className="font-semibold text-slate-800">Price</dt><dd className="mt-1 text-slate-600">{product.price ? `INR ${product.price.amount.toLocaleString("en-IN")}` : "Not listed"}</dd></div><div><dt className="font-semibold text-slate-800">Price checked</dt><dd className="mt-1 text-slate-600">{formatDate(product.price_checked_at)}</dd></div><div><dt className="font-semibold text-slate-800">Availability</dt><dd className="mt-1 text-slate-600">{displayCode(product.availability_status)} in {product.country_codes.join(", ") || "unspecified locations"}</dd></div><div><dt className="font-semibold text-slate-800">Availability checked</dt><dd className="mt-1 text-slate-600">{formatDate(product.availability_checked_at)}</dd></div><div><dt className="font-semibold text-slate-800">Fragrance</dt><dd className="mt-1 text-slate-600">{displayCode(product.fragrance_status)}</dd></div></dl>{product.price_is_stale || product.availability_is_stale ? <p className="mt-5 flex gap-2 text-xs leading-5 text-amber-800"><CalendarClock className="h-4 w-4 shrink-0" /> This snapshot is older than the configured freshness window.</p> : null}</section>
          <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"><h2 className="font-bold text-slate-950">Source summary</h2><p className="mt-2 text-sm text-slate-600">{product.source_name}</p><p className="mt-2 text-xs text-slate-500">Verified or created: {formatDate(product.source_verified_at)}</p>{product.official_product_url ? <a href={product.official_product_url} target="_blank" rel="noreferrer" className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-brand-700">Official product page <ExternalLink className="h-4 w-4" /></a> : null}</section>
        </aside>
      </div>
      <DisclaimerBox title="General catalogue information only" description={product.general_disclaimer} />
    </section>
  );
}

