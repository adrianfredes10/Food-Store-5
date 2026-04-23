import { CardPayment, initMercadoPago } from "@mercadopago/sdk-react";
import { useEffect, useRef } from "react";

import { usePagoTarjeta } from "@/features/pagos/hooks/usePagoTarjeta";

const publicKey = import.meta.env.VITE_MP_PUBLIC_KEY ?? "";

type Props = {
  pedidoId: number;
  amount: number;
  payerEmail: string;
};

export function CardPaymentBrick({ pedidoId, amount, payerEmail }: Props) {
  const mutation = usePagoTarjeta();
  const inited = useRef(false);

  useEffect(() => {
    if (!publicKey || inited.current) return;
    initMercadoPago(publicKey, { locale: "es-AR" });
    inited.current = true;
  }, []);

  if (!publicKey) {
    return (
      <div className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        Definí <code className="rounded bg-amber-100 px-1">VITE_MP_PUBLIC_KEY</code> en{" "}
        <code className="rounded bg-amber-100 px-1">.env</code> para usar el brick de tarjeta de Mercado
        Pago.
      </div>
    );
  }

  return (
    <div className="mt-4 max-w-lg rounded-lg border border-slate-200 bg-white p-4">
      <CardPayment
        locale="es-AR"
        initialization={{
          amount,
          payer: { email: payerEmail },
        }}
        onSubmit={async (formData) => {
          const email = formData.payer?.email ?? payerEmail;
          await mutation.mutateAsync({
            pedidoId,
            token: formData.token,
            payment_method_id: formData.payment_method_id,
            payer_email: email,
            installments: formData.installments,
          });
        }}
        onError={() => {
          /* errores de validación del brick */
        }}
      />
      {mutation.isPending && (
        <p className="mt-3 text-sm text-slate-600" aria-live="polite">
          Procesando pago…
        </p>
      )}
    </div>
  );
}
