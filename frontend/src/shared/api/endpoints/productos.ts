import { apiClient } from "@/shared/api/client";

import type { ProductoIngredienteSalidaDTO } from "./ingredientes";

export const PRODUCTOS_LIST_PATH = "/productos";

export type ProductosQueryParams = {
  page?: number;
  size?: number;
  categoria_id?: number;
  incluir_subcategorias?: boolean;
  disponible?: boolean;
  search?: string;
};

export type ProductoListadoItemDTO = {
  id: number;
  categoria_id: number;
  nombre: string;
  descripcion: string | null;
  precio: string | number;
  disponible: boolean;
  stock_cantidad: number;
  sku: string | null;
  imagen_url: string | null;
  /** Si el backend lo envía en el listado: habilita el flujo de personalización en la tarjeta. */
  ingredientes?: ProductoIngredienteSalidaDTO[];
};

export type PaginaProductosDTO = {
  items: ProductoListadoItemDTO[];
  total: number;
  page: number;
  size: number;
  pages: number;
};

export async function getProductos(params: ProductosQueryParams): Promise<PaginaProductosDTO> {
  const { data } = await apiClient.get<PaginaProductosDTO>(PRODUCTOS_LIST_PATH, { params });
  return data;
}

export type ProductoCreateBody = {
  categoria_id: number;
  nombre: string;
  descripcion?: string | null;
  precio: number;
  sku?: string | null;
  imagen_url?: string | null;
  activo?: boolean;
  disponible?: boolean;
  stock_cantidad?: number;
  ingredientes?: unknown[];
};

export type ProductoReadDTO = {
  id: number;
  categoria_id: number;
  nombre: string;
  descripcion: string | null;
  precio: string | number;
  sku: string | null;
  imagen_url: string | null;
  activo: boolean;
  disponible: boolean;
  stock_cantidad: number;
  ingredientes: unknown[];
};

export type ProductoPatchBody = Partial<{
  categoria_id: number;
  nombre: string;
  descripcion: string | null;
  precio: number;
  sku: string | null;
  imagen_url: string | null;
  activo: boolean;
  disponible: boolean;
  ingredientes: unknown[];
}>;

export async function createProducto(body: ProductoCreateBody): Promise<ProductoReadDTO> {
  const { data } = await apiClient.post<ProductoReadDTO>(PRODUCTOS_LIST_PATH, body);
  return data;
}

export async function patchProducto(id: number, body: ProductoPatchBody): Promise<ProductoReadDTO> {
  const { data } = await apiClient.patch<ProductoReadDTO>(`${PRODUCTOS_LIST_PATH}/${id}`, body);
  return data;
}

export async function patchProductoStock(id: number, stock_cantidad: number): Promise<ProductoReadDTO> {
  const { data } = await apiClient.patch<ProductoReadDTO>(`${PRODUCTOS_LIST_PATH}/${id}/stock`, {
    stock_cantidad,
  });
  return data;
}

export async function deleteProducto(id: number): Promise<void> {
  await apiClient.delete(`${PRODUCTOS_LIST_PATH}/${id}`);
}
