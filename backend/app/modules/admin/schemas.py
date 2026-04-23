from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class VentaDiaPunto(BaseModel):
    fecha: str
    total: Decimal


class MetricasDashboardResponse(BaseModel):
    total_pedidos: int
    pedidos_por_estado: dict[str, int]
    ingresos_totales: Decimal
    ventas_por_dia: list[VentaDiaPunto]


class AdminPedidoListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    usuario_id: int
    estado: str
    total: Decimal
    moneda: str
    costo_envio: Decimal
    forma_pago_codigo: str | None = None
    created_at: datetime | None = None


class AdminPedidosPage(BaseModel):
    items: list[AdminPedidoListItem]
    total: int
    page: int
    size: int


class PedidoDetalleLinea(BaseModel):
    nombre_producto: str
    cantidad: int
    precio_unitario_snapshot: Decimal
    subtotal: Decimal


class PedidoAdminDetalleResponse(BaseModel):
    id: int
    usuario_id: int
    direccion_entrega_id: int | None
    estado: str
    total: Decimal
    moneda: str
    costo_envio: Decimal
    forma_pago_codigo: str | None = None
    dir_linea1: str | None = None
    dir_ciudad: str | None = None
    dir_provincia: str | None = None
    dir_cp: str | None = None
    dir_alias: str | None = None
    detalles: list[PedidoDetalleLinea]


class AdminPedidoTransicionRequest(BaseModel):
    estado: str = Field(min_length=1, max_length=32)
