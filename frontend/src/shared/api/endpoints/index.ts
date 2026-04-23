/**
 * Constantes de rutas API (sin lógica). Las llamadas van en features con TanStack Query + apiClient.
 */
export const endpoints = {
  auth: {
    login: "/auth/login",
    refresh: "/auth/refresh",
    logout: "/auth/logout",
  },
  productos: {
    list: "/productos",
    detail: (id: number) => `/productos/${id}`,
  },
  pagos: {
    checkout: (pedidoId: number) => `/pagos/checkout/pedidos/${pedidoId}`,
  },
} as const;
