import { apiClient } from "@/shared/api/client";

export const PEDIDOS_PATH = "/pedidos";

export type CrearPedidoItem = {
  producto_id: number;
  cantidad: number;
  personalizacion?: number[];
};

export type CrearPedidoBody = {
  items: CrearPedidoItem[];
  direccion_entrega_id?: number | null;
  forma_pago_codigo?: string;
};

export type PedidoCreadoResponse = {
  id: number;
  estado: string;
  total: string | number;
  moneda: string;
  costo_envio: string | number;
  forma_pago_codigo: string | null;
  dir_linea1?: string | null;
  dir_ciudad?: string | null;
  dir_provincia?: string | null;
  dir_cp?: string | null;
  dir_alias?: string | null;
};

export type PedidoResumenDTO = PedidoCreadoResponse & {
  direccion_entrega_id?: number | null;
};

export interface DetallePedidoRead {
  id: number;
  producto_id: number | null;
  nombre_producto: string;
  precio_unitario_snapshot: number;
  cantidad: number;
  subtotal: number;
  personalizacion: number[] | null;
}

export interface HistorialEstadoRead {
  id: number;
  pedido_id: number;
  estado_anterior: string | null;
  estado_nuevo: string;
  motivo: string | null;
  registrado_en: string;
  usuario_id: number | null;
}

export interface PedidoListadoItem {
  id: number;
  estado: string;
  total: number;
  costo_envio: number;
  created_at: string;
  cantidad_items: number;
}

export interface PedidoDetalleCliente {
  id: number;
  estado: string;
  total: number;
  costo_envio: number;
  forma_pago_codigo: string | null;
  dir_linea1: string | null;
  dir_alias: string | null;
  observaciones_cliente: string | null;
  created_at: string;
  detalles: DetallePedidoRead[];
}

export interface PaginaPedidosCliente {
  items: PedidoListadoItem[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export const pedidosClienteApi = {
  listar: (params?: { page?: number; size?: number; estado?: string }) =>
    apiClient.get<PaginaPedidosCliente>(PEDIDOS_PATH, { params }).then((r) => r.data),

  obtener: (id: number) =>
    apiClient.get<PedidoDetalleCliente>(`${PEDIDOS_PATH}/${id}`).then((r) => r.data),

  historial: (id: number) =>
    apiClient.get<HistorialEstadoRead[]>(`${PEDIDOS_PATH}/${id}/historial`).then((r) => r.data),

  cancelar: (id: number, motivo: string) =>
    apiClient
      .delete<PedidoDetalleCliente>(`${PEDIDOS_PATH}/${id}`, { data: { motivo } })
      .then((r) => r.data),
};

export async function crearPedido(data: CrearPedidoBody): Promise<PedidoCreadoResponse> {
  const { data: res } = await apiClient.post<PedidoCreadoResponse>(PEDIDOS_PATH, data);
  return res;
}

export async function getPedido(pedidoId: number): Promise<PedidoDetalleCliente> {
  const { data } = await apiClient.get<PedidoDetalleCliente>(`${PEDIDOS_PATH}/${pedidoId}`);
  return data;
}

export async function cancelarPedido(pedidoId: number, motivo: string): Promise<PedidoDetalleCliente> {
  return pedidosClienteApi.cancelar(pedidoId, motivo);
}
