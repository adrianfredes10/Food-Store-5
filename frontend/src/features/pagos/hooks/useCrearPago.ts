import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { pagosApi } from "@/shared/api/endpoints/pagos";

export function useIniciarCheckout() {
  return useMutation({
    mutationFn: (pedidoId: number) =>
      pagosApi.iniciarCheckout(pedidoId),
    onSuccess: (data) => {
      if (data.init_point) {
        window.location.href = data.init_point;
      }
    },
    onError: () => {
      toast.error("Error al iniciar el pago. Intentá de nuevo.");
    },
  });
}

export function useCrearPago() {
  return useIniciarCheckout();
}
