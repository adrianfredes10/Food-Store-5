import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  createDireccion,
  deleteDireccion,
  listDirecciones,
  marcarDireccionPrincipal,
  updateDireccion,
  type DireccionCreateBody,
  type DireccionUpdateBody,
} from "@/shared/api/endpoints/direcciones";
import { useAuthStore } from "@/shared/store/auth-store";

export function useDirecciones() {
  const token = useAuthStore((s) => s.access_token);
  return useQuery({
    queryKey: ["direcciones"] as const,
    queryFn: listDirecciones,
    enabled: Boolean(token),
  });
}

export function useDireccionesMutations() {
  const qc = useQueryClient();

  const crear = useMutation({
    mutationFn: (body: DireccionCreateBody) => createDireccion(body),
    onSuccess: () => {
      toast.success("Dirección guardada");
      void qc.invalidateQueries({ queryKey: ["direcciones"] });
    },
    onError: () => toast.error("No se pudo crear la dirección"),
  });

  const actualizar = useMutation({
    mutationFn: ({ id, body }: { id: number; body: DireccionUpdateBody }) => updateDireccion(id, body),
    onSuccess: () => {
      toast.success("Dirección actualizada");
      void qc.invalidateQueries({ queryKey: ["direcciones"] });
    },
    onError: () => toast.error("No se pudo actualizar"),
  });

  const eliminar = useMutation({
    mutationFn: (id: number) => deleteDireccion(id),
    onSuccess: () => {
      toast.success("Dirección eliminada");
      void qc.invalidateQueries({ queryKey: ["direcciones"] });
    },
    onError: () => toast.error("No se pudo eliminar"),
  });

  return { crear, actualizar, eliminar };
}

export function useMarcarPrincipal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (dir_id: number) => marcarDireccionPrincipal(dir_id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["direcciones"] });
    },
  });
}
