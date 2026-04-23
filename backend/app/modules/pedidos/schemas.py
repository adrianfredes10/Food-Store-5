from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field


class ItemPedidoCrear(BaseModel):
    producto_id: int = Field(ge=1)
    cantidad: int = Field(ge=1)
    personalizacion: list[int] | None = None


class CrearPedidoRequest(BaseModel):
    items: list[ItemPedidoCrear] = Field(min_length=1)
    direccion_entrega_id: int | None = Field(default=None, ge=1)
    observaciones_cliente: str | None = Field(default=None, max_length=500)
    forma_pago_codigo: str = "MERCADOPAGO"


class PedidoCreadoResponse(BaseModel):
    id: int
    estado: str
    total: Decimal
    moneda: str
    costo_envio: Decimal
    forma_pago_codigo: str | None
    dir_linea1: str | None = None
    dir_ciudad: str | None = None
    dir_provincia: str | None = None
    dir_cp: str | None = None
    dir_alias: str | None = None


class PedidoResumenResponse(BaseModel):
    """Detalle mínimo del pedido para el cliente autenticado."""

    id: int
    estado: str
    total: Decimal
    moneda: str
    direccion_entrega_id: int | None = None
    costo_envio: Decimal
    forma_pago_codigo: str | None = None
    dir_linea1: str | None = None
    dir_ciudad: str | None = None
    dir_provincia: str | None = None
    dir_cp: str | None = None
    dir_alias: str | None = None


class CancelarPedidoRequest(BaseModel):
    motivo: str = Field(min_length=1, max_length=500)


class DetallePedidoRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    producto_id: int | None
    nombre_producto: str
    precio_unitario_snapshot: Decimal
    cantidad: int
    subtotal: Decimal
    personalizacion: list[int] | None


class HistorialEstadoPedidoRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    pedido_id: int
    estado_anterior: str | None
    estado_nuevo: str
    motivo: str | None
    registrado_en: datetime
    usuario_id: int | None


class PedidoDetalleCliente(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    estado: str
    total: Decimal
    costo_envio: Decimal
    forma_pago_codigo: str | None
    dir_linea1: str | None
    dir_alias: str | None
    observaciones_cliente: str | None
    created_at: datetime
    detalles: list[DetallePedidoRead]


class PedidoListadoItem(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    estado: str
    total: Decimal
    costo_envio: Decimal
    created_at: datetime
    cantidad_items: int


class PaginaPedidosCliente(BaseModel):
    items: list[PedidoListadoItem]
    total: int
    page: int
    size: int
    pages: int
