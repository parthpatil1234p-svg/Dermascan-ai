import { Navigate, useLocation } from "react-router-dom";
import { ROUTES } from "../constants/appContent";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children }) {
  const location = useLocation();
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return (
      <Navigate
        to={ROUTES.login}
        state={{ from: location.pathname }}
        replace
      />
    );
  }

  return children;
}

