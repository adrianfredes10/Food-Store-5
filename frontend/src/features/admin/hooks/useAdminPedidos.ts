import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { adminTransicionPedido, getAdminPedido, getAdminPedidos } from "@/shared/api/endpoints/admin";

export function useAdminPedidosList(page: number) {
  // cargo los pedidos del back
  return useQuery({
    queryKey: ["admin", "pedidos", page] as const,
    queryFn: () => getAdminPedidos(page, 20),
  });
}

export function useAdminPedidoDetalle(id: number | null) {
  return useQuery({
    queryKey: ["admin", "pedido", id] as const,
    queryFn: () => getAdminPedido(id!),
    enabled: id !== null,
  });
}

export function useAdminPedidoTransicion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ pedidoId, estado }: { pedidoId: number; estado: string }) =>
      adminTransicionPedido(pedidoId, estado),
    onSuccess: (_data, vars) => {
      toast.success("Estado actualizado");
      // esto recarga la lista despues de guardar
      void qc.invalidateQueries({ queryKey: ["admin", "pedido", vars.pedidoId] });
      void qc.invalidateQueries({ queryKey: ["admin", "pedidos"] });
      void qc.invalidateQueries({ queryKey: ["admin", "dashboard"] });
    },
    onError: () => toast.error("Transición no permitida"),
  });
}
