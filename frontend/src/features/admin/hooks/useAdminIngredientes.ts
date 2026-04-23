import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  ingredientesApi,
  type IngredienteCreateBody,
  type IngredientePatchBody,
  type IngredienteRead,
} from "@/shared/api/endpoints/ingredientes";

const ADMIN_INGREDIENTES_TODOS_KEY = ["admin-ingredientes-todas"] as const;

// cargo todos los ingredientes del back paginando de a 100
async function listarTodosLosIngredientes(): Promise<IngredienteRead[]> {
  const size = 100;
  let page = 1;
  const all: IngredienteRead[] = [];
  let pages = 1;
  do {
    const r = await ingredientesApi.listar({ page, size });
    all.push(...r.items);
    pages = r.pages;
    page += 1;
  } while (page <= pages);
  return all;
}

/** Lista completa para admin (filtros solo en cliente). */
export function useIngredientesTodos() {
  return useQuery({
    queryKey: ADMIN_INGREDIENTES_TODOS_KEY,
    queryFn: listarTodosLosIngredientes,
  });
}

export function useIngredientes(params?: {
  page?: number;
  size?: number;
  es_alergeno?: boolean;
  search?: string;
}) {
  return useQuery({
    queryKey: ["ingredientes", params],
    queryFn: () => ingredientesApi.listar(params),
  });
}

export function useIngredientesDeProducto(productoId: number | null) {
  return useQuery({
    queryKey: ["producto-ingredientes", productoId],
    queryFn: () => ingredientesApi.listarDeProducto(productoId!),
    enabled: productoId !== null,
  });
}

export function useCrearIngrediente() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: IngredienteCreateBody) => ingredientesApi.crear(data),
    onSuccess: () => {
      // esto recarga la lista despues de guardar
      void qc.invalidateQueries({ queryKey: ["ingredientes"] });
      void qc.invalidateQueries({ queryKey: ADMIN_INGREDIENTES_TODOS_KEY });
    },
  });
}

export function useActualizarIngrediente() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: IngredientePatchBody }) =>
      ingredientesApi.actualizar(id, data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["ingredientes"] });
      void qc.invalidateQueries({ queryKey: ADMIN_INGREDIENTES_TODOS_KEY });
    },
  });
}

export function useEliminarIngrediente() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => ingredientesApi.eliminar(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["ingredientes"] });
      void qc.invalidateQueries({ queryKey: ADMIN_INGREDIENTES_TODOS_KEY });
    },
  });
}
