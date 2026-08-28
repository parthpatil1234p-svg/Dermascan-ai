import { Navigate } from "react-router-dom";
import { ROUTES } from "../constants/appContent";
import { useSkinConcern } from "../context/SkinConcernContext";

export default function ConcernRequiredRoute({ children }) {
  const { concernReport, isAnalyzing, isLoadingReport, canContinue } = useSkinConcern();

  if (isAnalyzing || isLoadingReport) {
    return (
      <section className="flex min-h-[55vh] items-center justify-center px-4">
        <div className="text-center" role="status">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
          <p className="mt-4 text-sm font-semibold text-slate-700">
            Confirming visible observation results...
          </p>
        </div>
      </section>
    );
  }

  if (!concernReport || !canContinue) {
    return <Navigate to={ROUTES.skinConcernAnalysis} replace />;
  }

  return children;
}
