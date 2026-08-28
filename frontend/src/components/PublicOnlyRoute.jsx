import { Navigate } from "react-router-dom";
import { ROUTES } from "../constants/appContent";
import { useAuth } from "../context/AuthContext";

export default function PublicOnlyRoute({ children }) {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to={ROUTES.skinProfile} replace />;
  }

  return children;
}

