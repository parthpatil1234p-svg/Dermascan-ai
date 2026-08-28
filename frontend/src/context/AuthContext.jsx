import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { clearStoredToken, getStoredToken, storeToken } from "../services/api";
import {
  getCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
} from "../services/authService";

const AuthContext = createContext(null);

function AuthLoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-clinic-50 px-4">
      <div className="rounded-lg border border-slate-200 bg-white p-6 text-center shadow-soft">
        <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
        <p className="mt-4 text-sm font-semibold text-slate-700">
          Checking secure session...
        </p>
      </div>
    </div>
  );
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => getStoredToken());
  const [isLoading, setIsLoading] = useState(true);

  const clearAuthState = useCallback(() => {
    clearStoredToken();
    setToken(null);
    setUser(null);
  }, []);

  const loadCurrentUser = useCallback(async () => {
    const storedToken = getStoredToken();

    if (!storedToken) {
      clearAuthState();
      setIsLoading(false);
      return;
    }

    setToken(storedToken);
    setIsLoading(true);

    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch {
      clearAuthState();
    } finally {
      setIsLoading(false);
    }
  }, [clearAuthState]);

  useEffect(() => {
    loadCurrentUser();
  }, [loadCurrentUser]);

  useEffect(() => {
    const handleUnauthorized = () => {
      clearAuthState();
    };

    window.addEventListener("dermascan:unauthorized", handleUnauthorized);
    return () =>
      window.removeEventListener("dermascan:unauthorized", handleUnauthorized);
  }, [clearAuthState]);

  const register = async (values) => {
    const authResponse = await registerUser(values);
    storeToken(authResponse.access_token);
    setToken(authResponse.access_token);
    setUser(authResponse.user);
    return authResponse;
  };

  const login = async (values) => {
    const authResponse = await loginUser(values);
    storeToken(authResponse.access_token);
    setToken(authResponse.access_token);
    setUser(authResponse.user);
    return authResponse;
  };

  const logout = useCallback(async () => {
    await logoutUser();
    clearAuthState();
  }, [clearAuthState]);

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(user && token),
      isLoading,
      register,
      login,
      logout,
      loadCurrentUser,
    }),
    [user, token, isLoading, loadCurrentUser, logout],
  );

  if (isLoading) {
    return <AuthLoadingScreen />;
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
