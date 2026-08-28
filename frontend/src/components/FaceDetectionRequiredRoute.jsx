import { Navigate } from "react-router-dom";
import { ROUTES } from "../constants/appContent";
import { useFaceDetection } from "../context/FaceDetectionContext";

export default function FaceDetectionRequiredRoute({ children }) {
  const { canContinue, faceReport, isDetecting } = useFaceDetection();

  if (isDetecting) {
    return (
      <section className="flex min-h-[55vh] items-center justify-center px-4">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
          <p className="mt-4 text-sm font-semibold text-slate-700">
            Confirming face-detection permission...
          </p>
        </div>
      </section>
    );
  }

  if (!faceReport || !canContinue) {
    return <Navigate to={ROUTES.faceDetection} replace />;
  }

  return children;
}
