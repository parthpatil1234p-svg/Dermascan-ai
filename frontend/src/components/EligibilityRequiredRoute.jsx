import { Navigate } from "react-router-dom";
import { ROUTES } from "../constants/appContent";
import { useProductEligibility } from "../context/ProductEligibilityContext";

export default function EligibilityRequiredRoute({ children }) {
  const { eligibilityReport, isEvaluating, isLoadingReport } = useProductEligibility();

  if (isEvaluating || isLoadingReport) {
    return (
      <section className="flex min-h-[55vh] items-center justify-center px-4">
        <div className="text-center" role="status">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
          <p className="mt-4 text-sm font-semibold text-slate-700">
            Confirming product eligibility results...
          </p>
        </div>
      </section>
    );
  }

  if (!eligibilityReport) {
    return <Navigate to={ROUTES.productEligibility} replace />;
  }

  return children;
}
