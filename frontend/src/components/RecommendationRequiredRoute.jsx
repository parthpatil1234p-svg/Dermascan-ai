import { Navigate } from "react-router-dom";
import { ROUTES } from "../constants/appContent";
import { useProductRecommendation } from "../context/ProductRecommendationContext";


export default function RecommendationRequiredRoute({ children }) {
  const { recommendationReport, isGenerating, isLoadingReport } = useProductRecommendation();
  if (isGenerating || isLoadingReport) return <div className="flex min-h-[55vh] items-center justify-center" role="status"><p className="font-semibold text-slate-700">Confirming recommendations...</p></div>;
  if (!recommendationReport?.can_continue) return <Navigate to={ROUTES.productRecommendations} replace />;
  return children;
}
