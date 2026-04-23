import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { pedidosClienteApi } from "@/shared/api/endpoints/pedidos";

export function useMisPedidos(params?: { page?: number; estado?: string }) {
  // cargo los pedidos del back
  return useQuery({
    queryKey: ["mis-pedidos", params],
    queryFn: () => pedidosClienteApi.listar(params),
  });
}

export function usePedidoDetalle(pedidoId: number | null) {
  return useQuery({
    queryKey: ["pedido", pedidoId],
    queryFn: () => pedidosClienteApi.obtener(pedidoId!),
    enabled: pedidoId !== null,
    refetchInterval: (query) => {
      const estado = query.state.data?.estado;
      if (estado === "ENTREGADO" || estado === "CANCELADO") return false;
      return 30_000;
    },
  });
}

export function usePedidoHistorial(pedidoId: number | null) {
  return useQuery({
    queryKey: ["pedido-historial", pedidoId],
    queryFn: () => pedidosClienteApi.historial(pedidoId!),
    enabled: pedidoId !== null,
  });
}

export function useCancelarPedido() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, motivo }: { id: number; motivo: string }) =>
      pedidosClienteApi.cancelar(id, motivo),
    onSuccess: (_, { id }) => {
      // esto recarga la lista despues de guardar
      void qc.invalidateQueries({ queryKey: ["mis-pedidos"] });
      void qc.invalidateQueries({ queryKey: ["pedido", id] });
      void qc.invalidateQueries({ queryKey: ["pedido-historial", id] });
    },
  });
}
