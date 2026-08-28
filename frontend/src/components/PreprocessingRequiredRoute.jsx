import { Navigate } from "react-router-dom";
import { ROUTES } from "../constants/appContent";
import { useImagePreprocessing } from "../context/ImagePreprocessingContext";

export default function PreprocessingRequiredRoute({ children }) {
  const { canContinue, isProcessing, preprocessingReport } =
    useImagePreprocessing();

  if (isProcessing) {
    return (
      <section className="flex min-h-[55vh] items-center justify-center px-4">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
          <p className="mt-4 text-sm font-semibold text-slate-700">
            Confirming model-input readiness...
          </p>
        </div>
      </section>
    );
  }

  if (!preprocessingReport || !canContinue) {
    return <Navigate to={ROUTES.imagePreprocessing} replace />;
  }

  return children;
}
