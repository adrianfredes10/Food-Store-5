import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  categoriasApi,
  type CategoriaCreateBody,
  type CategoriaPatchBody,
  type CategoriaRead,
} from "@/shared/api/endpoints/categorias";

const QUERY_KEY = ["admin-categorias-todas"] as const;

// cargo todas las categorias del back paginando de a 100
async function listarTodasLasCategorias(): Promise<CategoriaRead[]> {
  const size = 100;
  let page = 1;
  const all: CategoriaRead[] = [];
  let pages = 1;
  do {
    const r = await categoriasApi.listar({ page, size });
    all.push(...r.items);
    pages = r.pages;
    page += 1;
  } while (page <= pages);
  return all;
}

export type CategoriaNodo = CategoriaRead & { hijos: CategoriaNodo[] };

/** Construye árbol desde lista plana (parent_id). */
export function buildCategoriaArbol(flat: CategoriaRead[]): CategoriaNodo[] {
  const map = new Map<number, CategoriaNodo>();
  for (const c of flat) {
    map.set(c.id, { ...c, hijos: [] });
  }
  const roots: CategoriaNodo[] = [];
  for (const c of flat) {
    const node = map.get(c.id)!;
    if (c.parent_id == null || !map.has(c.parent_id)) {
      roots.push(node);
    } else {
      map.get(c.parent_id)!.hijos.push(node);
    }
  }
  function sortRec(nodes: CategoriaNodo[]) {
    nodes.sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
    for (const n of nodes) sortRec(n.hijos);
  }
  sortRec(roots);
  return roots;
}

/** Para selects con indentación por nivel. */
export function aplanarCategoriasParaSelect(
  nodos: CategoriaNodo[],
  nivel = 0,
): { id: number; label: string }[] {
  const out: { id: number; label: string }[] = [];
  const pad = "  ".repeat(nivel);
  for (const n of nodos) {
    out.push({ id: n.id, label: pad + n.nombre });
    out.push(...aplanarCategoriasParaSelect(n.hijos, nivel + 1));
  }
  return out;
}

export function useCategorias() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: listarTodasLasCategorias,
  });
}

export function useCrearCategoria() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CategoriaCreateBody) => categoriasApi.crear(data),
    onSuccess: () => {
      // esto recarga la lista despues de guardar
      void qc.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useActualizarCategoria() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: CategoriaPatchBody }) =>
      categoriasApi.actualizar(id, data),
    onSuccess: () => {
      // esto recarga la lista despues de guardar
      void qc.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useEliminarCategoria() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => categoriasApi.eliminar(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}
