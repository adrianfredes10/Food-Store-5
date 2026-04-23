import { apiClient } from "@/shared/api/client";

export interface IngredienteRead {
  id: number;
  nombre: string;
  unidad: string | null;
  es_alergeno: boolean;
}

export interface PaginaIngredientes {
  items: IngredienteRead[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

/** Misma forma que el backend (`ProductoIngredienteSalida`). */
export interface ProductoIngredienteSalidaDTO {
  ingrediente_id: number;
  nombre: string;
  es_alergeno: boolean;
  cantidad: string | number;
  es_removible: boolean;
}

export type IngredienteCreateBody = {
  nombre: string;
  unidad?: string | null;
  es_alergeno?: boolean;
};

export type IngredientePatchBody = Partial<{
  nombre: string;
  unidad: string | null;
  es_alergeno: boolean;
}>;

export const ingredientesApi = {
  listar: (params?: { page?: number; size?: number; es_alergeno?: boolean; search?: string }) =>
    apiClient.get<PaginaIngredientes>("/ingredientes", { params }).then((r) => r.data),

  obtener: (id: number) => apiClient.get<IngredienteRead>(`/ingredientes/${id}`).then((r) => r.data),

  listarDeProducto: (productoId: number) =>
    apiClient
      .get<ProductoIngredienteSalidaDTO[]>(`/productos/${productoId}/ingredientes`)
      .then((r) => r.data),

  crear: (data: IngredienteCreateBody) =>
    apiClient.post<IngredienteRead>("/ingredientes", data).then((r) => r.data),

  actualizar: (id: number, data: IngredientePatchBody) =>
    apiClient.patch<IngredienteRead>(`/ingredientes/${id}`, data).then((r) => r.data),

  eliminar: (id: number) => apiClient.delete(`/ingredientes/${id}`),
};
