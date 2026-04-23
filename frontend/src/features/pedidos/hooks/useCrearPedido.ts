import { useMutation, useQueryClient } from "@tanstack/react-query";

import { crearPedido, type CrearPedidoBody } from "@/shared/api/endpoints/pedidos";

export function useCrearPedido() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (body: CrearPedidoBody) => crearPedido(body),
    onSuccess: () => {
      // esto recarga la lista despues de guardar
      void qc.invalidateQueries({ queryKey: ["productos"] });
      void qc.invalidateQueries({ queryKey: ["direcciones"] });
      void qc.invalidateQueries({ queryKey: ["mis-pedidos"] });
    },
  });
}
