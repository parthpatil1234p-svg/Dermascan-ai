import { Info } from "lucide-react";
import PageHeader from "../components/PageHeader";
import ProductCatalogue from "../components/ProductCatalogue";

export default function ProductsPage() {
  return (
    <section className="py-12">
      <div className="px-4 sm:px-6"><PageHeader eyebrow="Structured product catalogue" title="Explore Skincare Product Data" description="Search factual catalogue fields, cautious skin-goal mappings, ingredient metadata, and dated price and availability snapshots." /></div>
      <div className="mx-auto mb-6 flex max-w-7xl items-start gap-3 border-y border-clinic-100 bg-clinic-50 px-4 py-4 text-sm leading-6 text-slate-700 sm:px-6"><Info className="mt-0.5 h-5 w-5 shrink-0 text-clinic-700" aria-hidden="true" /><p><strong>Catalogue Search Only.</strong> Personalized ranking will be added in the next development step. Matching results are not medical recommendations.</p></div>
      <ProductCatalogue />
    </section>
  );
}

