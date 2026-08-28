import { Navigate } from "react-router-dom";
import { ROUTES } from "../constants/appContent";
import { useSkincareRoutine } from "../context/SkincareRoutineContext";


export default function RoutineRequiredRoute({ children }) {
  const { routineReport, isGenerating } = useSkincareRoutine();
  if (isGenerating) return <div className="flex min-h-[55vh] items-center justify-center" role="status"><p className="font-semibold text-slate-700">Confirming routine report...</p></div>;
  if (!routineReport?.can_continue) return <Navigate to={ROUTES.skincareRoutine} replace />;
  return children;
}
