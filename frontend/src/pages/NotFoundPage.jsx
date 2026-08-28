import { Home, ScanFace } from "lucide-react";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import { ROUTES } from "../constants/appContent";

export default function NotFoundPage() {
  return (
    <section className="px-4 py-20 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl">
        <PageHeader
          eyebrow="404"
          title="Page not found"
          description="The page you are looking for does not exist in DermaScan AI."
        />
        <div className="rounded-lg border border-slate-200 bg-white p-8 text-center shadow-soft">
          <p className="text-sm leading-6 text-slate-600">
            You can return to the homepage or continue the guided analysis flow.
          </p>
        </div>
        <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
          <SecondaryButton to={ROUTES.home} icon={Home}>
            Return to Home
          </SecondaryButton>
          <PrimaryButton to={ROUTES.skinProfile} icon={ScanFace}>
            Start Analysis
          </PrimaryButton>
        </div>
      </div>
    </section>
  );
}
