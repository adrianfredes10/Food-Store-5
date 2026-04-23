import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import { registerRequest, type RegisterBody } from "@/shared/api/endpoints/auth";

export function useRegister(onRegistered: () => void) {
  return useMutation({
    mutationFn: (body: RegisterBody) => registerRequest(body),
    onSuccess: () => {
      toast.success("Cuenta creada. Ya podés iniciar sesión.");
      onRegistered();
    },
    onError: () => {
      // si falla muestro el error en un toast
      toast.error("No se pudo registrar (email en uso o datos inválidos).");
    },
  });
}
