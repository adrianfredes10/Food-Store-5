import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { useAuthStore } from "@/shared/store/auth-store";

/**
 * - Sin variable: `/api` → Vite reescribe a `/api/v1` en el backend (spec v5).
 * - URL absoluta: origen del backend; si termina en `/api` o `/api/v1` se normaliza.
 */
function resolveApiBase(): string {
  const raw =
    import.meta.env.VITE_API_BASE_URL?.trim() || import.meta.env.VITE_API_URL?.trim();
  if (!raw) return "/api";
  const noTrail = raw.replace(/\/+$/, "");
  if (noTrail.startsWith("http")) {
    if (noTrail.endsWith("/api/v1")) {
      return noTrail;
    }
    if (noTrail.endsWith("/api")) {
      return `${noTrail}/v1`;
    }
    return `${noTrail}/api/v1`;
  }
  return noTrail.startsWith("/") ? noTrail : `/api`;
}

const baseURL = resolveApiBase();

// configuro el cliente axios con la url base del back
export const apiClient = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().access_token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const { refresh_token, setTokens, logout } = useAuthStore.getState();

      if (refresh_token) {
        try {
          // Usamos axios directamente para evitar el interceptor de request que añade el Bearer viejo
          // o simplemente dejamos que el backend lo ignore si el body tiene el refresh_token.
          const res = await axios.post(`${baseURL}/auth/refresh`, { refresh_token });
          const { access_token, refresh_token: newRefresh } = res.data;

          setTokens(access_token, newRefresh);

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return apiClient(originalRequest);
        } catch (refreshError) {
          logout();
          if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
            window.location.assign("/login");
          }
          return Promise.reject(refreshError);
        }
      } else {
        const hadSession = Boolean(useAuthStore.getState().access_token);
        if (hadSession) {
          logout();
          if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
            window.location.assign("/login");
          }
        }
      }
    }
    return Promise.reject(error);
  },
);
