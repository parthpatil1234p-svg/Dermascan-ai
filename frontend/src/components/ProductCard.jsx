import { CalendarClock, MapPin, Tag } from "lucide-react";
import { Link } from "react-router-dom";
import { displayCode } from "../constants/catalogueOptions";

function formatDate(value) {
  return value ? new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" }).format(new Date(value)) : "Not recorded";
}

export default function ProductCard({ product }) {
  return (
    <article className="flex h-full flex-col rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-brand-700">{product.brand_name}</p>
          <h2 className="mt-1 text-lg font-bold text-slate-950">{product.product_name}</h2>
          <p className="mt-1 text-sm text-slate-500">{product.category_display}</p>
        </div>
        {product.is_demo_product ? (
          <span className="shrink-0 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-bold text-amber-900">Demo</span>
        ) : null}
      </div>

      <p className="mt-4 text-sm leading-6 text-slate-600">{product.short_description}</p>

      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="flex items-center gap-1.5 font-semibold text-slate-800"><Tag className="h-4 w-4" aria-hidden="true" /> Price</dt>
          <dd className="mt-1 text-slate-600">{product.price ? `INR ${product.price.amount.toLocaleString("en-IN")}` : "Not listed"}</dd>
        </div>
        <div>
          <dt className="flex items-center gap-1.5 font-semibold text-slate-800"><MapPin className="h-4 w-4" aria-hidden="true" /> Availability</dt>
          <dd className="mt-1 text-slate-600">{displayCode(product.availability_status)}</dd>
        </div>
      </dl>

      <div className="mt-4 flex flex-wrap gap-2">
        {product.suitable_skin_types.slice(0, 3).map((value) => (
          <span key={value} className="rounded-full bg-clinic-50 px-2.5 py-1 text-xs font-semibold text-clinic-800">{displayCode(value)}</span>
        ))}
      </div>

      {product.highlighted_ingredients.length ? (
        <p className="mt-4 text-sm text-slate-600"><span className="font-semibold text-slate-800">Highlights:</span> {product.highlighted_ingredients.join(", ")}</p>
      ) : null}
      <p className="mt-2 text-xs text-slate-500">Fragrance: {displayCode(product.fragrance_status)}</p>

      {(product.price_is_stale || product.availability_is_stale) ? (
        <p className="mt-3 flex items-start gap-2 text-xs leading-5 text-amber-800">
          <CalendarClock className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          Catalogue snapshot may be stale. Price or availability may have changed since {formatDate(product.price_checked_at)}.
        </p>
      ) : null}

      <Link
        to={`/products/${product.product_id}`}
        className="mt-5 inline-flex min-h-11 items-center justify-center rounded-lg border border-brand-600 px-4 py-2 text-sm font-semibold text-brand-700 transition hover:bg-brand-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
      >
        View Details
      </Link>
    </article>
  );
}

