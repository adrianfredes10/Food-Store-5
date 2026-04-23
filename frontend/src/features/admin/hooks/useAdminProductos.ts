import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { toast } from "sonner";

import {
  createProducto,
  deleteProducto,
  patchProducto,
  patchProductoStock,
  type ProductoCreateBody,
  type ProductoPatchBody,
} from "@/shared/api/endpoints/productos";

export function useActualizarProducto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ProductoPatchBody }) =>
      patchProducto(id, data),
    onSuccess: () => {
      // esto recarga la lista despues de guardar
      void qc.invalidateQueries({ queryKey: ["productos"] });
    },
  });
}

export function useAdminProductoMutations() {
  const qc = useQueryClient();

  const crear = useMutation({
    // mando el producto nuevo al back
    mutationFn: (body: ProductoCreateBody) => createProducto(body),
    onSuccess: () => {
      toast.success(
        "Producto creado. Si usás imagen automática (Groq), puede tardar unos segundos en verse: recargamos el catálogo automáticamente.",
      );
      // esto recarga la lista despues de guardar
      void qc.invalidateQueries({ queryKey: ["productos"] });
      // La API guarda la imagen en BackgroundTasks después de responder; sin esto casi siempre ves imagen_url vacía.
      window.setTimeout(() => void qc.invalidateQueries({ queryKey: ["productos"] }), 4000);
      window.setTimeout(() => void qc.invalidateQueries({ queryKey: ["productos"] }), 10000);
    },
    onError: (err) => {
      // si falla muestro el error en un toast
      if (axios.isAxiosError(err) && err.response?.status === 403) {
        toast.error("No tenés permiso de administrador para crear productos.");
        return;
      }
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        toast.error("Sesión vencida. Volvé a iniciar sesión como admin.");
        return;
      }
      if (axios.isAxiosError(err) && err.response === undefined) {
        toast.error("No hay conexión con la API. Revisá que el backend esté en marcha y la URL en .env.");
        return;
      }
      const respData = axios.isAxiosError(err) ? err.response?.data : undefined;
      const detail =
        typeof respData === "object" && respData !== null && "detail" in respData
          ? String((respData as { detail: unknown }).detail)
          : err instanceof Error
            ? err.message
            : null;
      toast.error(detail ? `No se pudo crear: ${detail}` : "No se pudo crear el producto");
    },
  });

  const patch = useMutation({
    mutationFn: ({ id, body }: { id: number; body: ProductoPatchBody }) => patchProducto(id, body),
    onSuccess: () => {
      toast.success("Producto actualizado");
      // esto recarga la lista despues de guardar
      void qc.invalidateQueries({ queryKey: ["productos"] });
    },
    onError: () => toast.error("Error al actualizar"),
  });

  const stock = useMutation({
    mutationFn: ({ id, stock_cantidad }: { id: number; stock_cantidad: number }) =>
      patchProductoStock(id, stock_cantidad),
    onSuccess: () => {
      toast.success("Stock actualizado");
      void qc.invalidateQueries({ queryKey: ["productos"] });
    },
    onError: () => toast.error("Stock inválido"),
  });

  const eliminar = useMutation({
    mutationFn: (id: number) => deleteProducto(id),
    onSuccess: () => {
      toast.success("Producto eliminado");
      void qc.invalidateQueries({ queryKey: ["productos"] });
    },
    onError: () => toast.error("No se pudo eliminar"),
  });

  return { crear, patch, stock, eliminar };
}
