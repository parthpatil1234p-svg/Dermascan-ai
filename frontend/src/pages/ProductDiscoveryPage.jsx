import { ShieldCheck } from "lucide-react";
import PageHeader from "../components/PageHeader";
import ProductCatalogue from "../components/ProductCatalogue";

export default function ProductDiscoveryPage() {
  return (
    <section className="py-12">
      <div className="px-4 sm:px-6"><PageHeader eyebrow="Authenticated workflow" title="Catalogue Product Discovery" description="Your analysis workflow is complete. Browse the same structured catalogue here without personalized scoring or hidden ranking." /></div>
      <div className="mx-auto mb-6 flex max-w-7xl items-start gap-3 border-y border-amber-200 bg-amber-50 px-4 py-4 text-sm leading-6 text-amber-950 sm:px-6"><ShieldCheck className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" /><p><strong>Catalogue Search Only.</strong> This view does not apply your private profile. Use the eligibility and recommendation reports for the protected personalized workflow.</p></div>
      <ProductCatalogue />
    </section>
  );
}
