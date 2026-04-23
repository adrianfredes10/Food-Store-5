import { apiClient } from "@/shared/api/client";

export type VentaDiaDTO = { fecha: string; total: string | number };
export type MetricasDashboardDTO = {
  total_pedidos: number;
  pedidos_por_estado: Record<string, number>;
  ingresos_totales: string | number;
  ventas_por_dia: VentaDiaDTO[];
};

export type AdminPedidoItemDTO = {
  id: number;
  usuario_id: number;
  estado: string;
  total: string | number;
  moneda: string;
  created_at?: string | null;
};

export type AdminPedidosPageDTO = {
  items: AdminPedidoItemDTO[];
  total: number;
  page: number;
  size: number;
};

export type PedidoDetalleLineaDTO = {
  nombre_producto: string;
  cantidad: number;
  precio_unitario_snapshot: string | number;
  subtotal: string | number;
};

export type PedidoAdminDetalleDTO = {
  id: number;
  usuario_id: number;
  direccion_entrega_id: number | null;
  estado: string;
  total: string | number;
  moneda: string;
  detalles: PedidoDetalleLineaDTO[];
};

export async function getAdminDashboard(): Promise<MetricasDashboardDTO> {
  const { data } = await apiClient.get<MetricasDashboardDTO>("/admin/dashboard");
  return data;
}

export async function getAdminPedidos(page = 1, size = 20): Promise<AdminPedidosPageDTO> {
  const { data } = await apiClient.get<AdminPedidosPageDTO>("/admin/pedidos", { params: { page, size } });
  return data;
}

export async function getAdminPedido(id: number): Promise<PedidoAdminDetalleDTO> {
  const { data } = await apiClient.get<PedidoAdminDetalleDTO>(`/admin/pedidos/${id}`);
  return data;
}

export async function adminTransicionPedido(
  pedidoId: number,
  estado: string,
): Promise<PedidoAdminDetalleDTO> {
  const { data } = await apiClient.post<PedidoAdminDetalleDTO>(
    `/admin/pedidos/${pedidoId}/transicion`,
    { estado },
  );
  return data;
}
