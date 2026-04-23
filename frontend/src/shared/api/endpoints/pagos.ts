import { apiClient } from "@/shared/api/client";

export type CheckoutPagoResponse = {
  pago_id: number;
  external_reference: string;
  preference_id: string;
  init_point: string;
  estado: string;
};

export type CrearCheckoutPagoOptions = {
  idempotencyKey?: string;
};

export const pagosApi = {
  iniciarCheckout: (pedidoId: number) =>
    apiClient.post<CheckoutPagoResponse>(`/pagos/checkout/pedidos/${pedidoId}`).then((r) => r.data),
};

export async function crearCheckoutPago(
  pedidoId: number,
  options?: CrearCheckoutPagoOptions,
): Promise<{ init_point: string }> {
  const headers: Record<string, string> = {};
  if (options?.idempotencyKey?.trim()) {
    headers["Idempotency-Key"] = options.idempotencyKey.trim();
  }
  const { data } = await apiClient.post<CheckoutPagoResponse>(
    `/pagos/checkout/pedidos/${pedidoId}`,
    {},
    { headers },
  );
  return { init_point: data.init_point };
}

export type PagoTarjetaBody = {
  pedido_id: number;
  token: string;
  payment_method_id: string;
  payer_email: string;
  installments?: number;
};

export type PagoTarjetaResponseDTO = {
  pago_id: number;
  estado: string;
  mp_status: string | null;
  mp_payment_id: string | null;
};

export async function crearPagoTarjeta(
  body: PagoTarjetaBody,
  idempotencyKey?: string,
): Promise<PagoTarjetaResponseDTO> {
  const headers: Record<string, string> = {};
  if (idempotencyKey?.trim()) {
    headers["Idempotency-Key"] = idempotencyKey.trim();
  }
  const { data } = await apiClient.post<PagoTarjetaResponseDTO>("/pagos/tarjeta", body, { headers });
  return data;
}
