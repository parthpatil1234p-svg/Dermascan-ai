import axios from "axios";

export const AUTH_TOKEN_KEY = "dermascan_access_token";

export function getStoredToken() {
  return typeof window === "undefined"
    ? null
    : window.localStorage.getItem(AUTH_TOKEN_KEY);
}

export function storeToken(token) {
  window.localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearStoredToken() {
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
}

function resolveApiBaseUrl() {
  const envUrl =
    import.meta.env.VITE_API_BASE_URL ||
    import.meta.env.VITE_API_URL;

  if (envUrl && typeof envUrl === "string" && envUrl.trim() !== "") {
    const cleanUrl = envUrl.trim().replace(/\/+$/, "");
    return cleanUrl.endsWith("/api") ? cleanUrl : `${cleanUrl}/api`;
  }

  // When running on localhost / 127.0.0.1, use Vite proxy '/api' so local requests route to backend
  if (
    typeof window !== "undefined" &&
    (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ) {
    return "/api";
  }

  return "https://dermascan-ai-5i1v.onrender.com/api";
}

const api = axios.create({
  baseURL: resolveApiBaseUrl(),
  timeout: 90000,
});

api.interceptors.request.use((config) => {
  const token = getStoredToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Bypass Localtunnel reminder page for automated API requests
  config.headers["bypass-tunnel-reminder"] = "true";

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error details:", {
      message: error.message,
      url: error.config?.url,
      baseURL: error.config?.baseURL,
      status: error.response?.status,
      data: error.response?.data,
    });

    if (error.response?.status === 401) {
      clearStoredToken();
      window.dispatchEvent(new Event("dermascan:unauthorized"));
    }

    return Promise.reject(error);
  },
);

export default api;
