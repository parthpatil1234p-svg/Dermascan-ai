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
    import.meta.env.VITE_API_URL ||
    "https://dermascan-ai-5i1v.onrender.com/api";

  const cleanUrl = envUrl.trim().replace(/\/+$/, "");
  return cleanUrl.endsWith("/api") ? cleanUrl : `${cleanUrl}/api`;
}

const api = axios.create({
  baseURL: resolveApiBaseUrl(),
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = getStoredToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

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
