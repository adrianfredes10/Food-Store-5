import { apiClient } from "@/shared/api/client";

export interface CategoriaRead {
  id: number;
  parent_id: number | null;
  nombre: string;
  descripcion: string | null;
  orden: number;
  activo: boolean;
}

export interface PaginaCategorias {
  items: CategoriaRead[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export type CategoriaCreateBody = {
  nombre: string;
  parent_id?: number | null;
  descripcion?: string | null;
  orden?: number;
  activo?: boolean;
};

export type CategoriaPatchBody = Partial<{
  nombre: string;
  parent_id: number | null;
  descripcion: string | null;
  orden: number;
  activo: boolean;
}>;

export const categoriasApi = {
  listar: (params?: {
    page?: number;
    size?: number;
    parent_id?: number | null;
    solo_raices?: boolean;
    activo?: boolean | null;
  }) => apiClient.get<PaginaCategorias>("/categorias", { params }).then((r) => r.data),

  obtener: (id: number) => apiClient.get<CategoriaRead>(`/categorias/${id}`).then((r) => r.data),

  crear: (data: CategoriaCreateBody) =>
    apiClient.post<CategoriaRead>("/categorias", data).then((r) => r.data),

  actualizar: (id: number, data: CategoriaPatchBody) =>
    apiClient.patch<CategoriaRead>(`/categorias/${id}`, data).then((r) => r.data),

  eliminar: (id: number) => apiClient.delete(`/categorias/${id}`),
};
