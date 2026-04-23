import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import { toast } from "sonner";

import { crearPagoTarjeta } from "@/shared/api/endpoints/pagos";

type Vars = {
  pedidoId: number;
  token: string;
  payment_method_id: string;
  payer_email: string;
  installments?: number;
};

export function usePagoTarjeta() {
  const qc = useQueryClient();
  const idempotencyRef = useRef(crypto.randomUUID());

  return useMutation({
    mutationFn: (vars: Vars) =>
      crearPagoTarjeta(
        {
          pedido_id: vars.pedidoId,
          token: vars.token,
          payment_method_id: vars.payment_method_id,
          payer_email: vars.payer_email,
          installments: vars.installments,
        },
        idempotencyRef.current,
      ),
    onSuccess: (_, vars) => {
      toast.success("Pago procesado");
      void qc.invalidateQueries({ queryKey: ["pedido", vars.pedidoId] });
      void qc.invalidateQueries({ queryKey: ["productos"] });
    },
    onError: () => {
      toast.error("El pago no pudo completarse");
    },
  });
}
