"""Consultas y orquestación del panel admin. Sin commit."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.enums import EstadoPedido
from app.modules.admin.schemas import (
    AdminPedidoListItem,
    AdminPedidosPage,
    MetricasDashboardResponse,
    PedidoAdminDetalleResponse,
    PedidoDetalleLinea,
    VentaDiaPunto,
)
from app.modules.pedidos.exceptions import PedidoNoEncontradoError
from app.modules.pedidos.model import DetallePedido, Pedido
from app.modules.pedidos.service import PedidoService

if TYPE_CHECKING:
    from app.core.uow.unit_of_work import UnitOfWork


def obtener_metricas_dashboard(uow: UnitOfWork) -> MetricasDashboardResponse:
    # junto todas las métricas que necesita el dashboard
    total = uow.pedidos.count_all()
    por_estado = uow.pedidos.count_group_by_estado()
    ingresos = uow.pedidos.sum_total_entregados()
    ventas_raw = uow.pedidos.ventas_diarias_entregados(30)
    ventas = [VentaDiaPunto(fecha=f, total=t) for f, t in ventas_raw]
    return MetricasDashboardResponse(
        total_pedidos=total,
        pedidos_por_estado=por_estado,
        ingresos_totales=ingresos,
        ventas_por_dia=ventas,
    )


def listar_pedidos_admin(uow: UnitOfWork, *, page: int, size: int) -> AdminPedidosPage:
    # 1. calculo el offset según la página pedida
    total = uow.pedidos.count_all()
    offset = (page - 1) * size
    rows = uow.pedidos.list_all_ordered_desc(offset, size)
    items: list[AdminPedidoListItem] = []
    for p in rows:
        assert p.id is not None
        items.append(
            AdminPedidoListItem(
                id=p.id,
                usuario_id=p.usuario_id,
                estado=p.estado.value,
                total=p.total,
                moneda=p.moneda,
                costo_envio=p.costo_envio,
                forma_pago_codigo=p.forma_pago_codigo,
                created_at=p.created_at,
            ),
        )
    return AdminPedidosPage(items=items, total=total, page=page, size=size)


def obtener_pedido_admin(uow: UnitOfWork, pedido_id: int) -> PedidoAdminDetalleResponse:
    # busco el pedido y sus líneas de detalle
    p = uow.pedidos.get_by_id(pedido_id)
    if p is None:
        raise PedidoNoEncontradoError(pedido_id)
    assert p.id is not None
    detalles_orm = uow.pedidos.list_detalles_por_pedido_id(pedido_id)
    detalles = [_map_detalle(d) for d in detalles_orm]
    return PedidoAdminDetalleResponse(
        id=p.id,
        usuario_id=p.usuario_id,
        direccion_entrega_id=p.direccion_entrega_id,
        estado=p.estado.value,
        total=p.total,
        moneda=p.moneda,
        costo_envio=p.costo_envio,
        forma_pago_codigo=p.forma_pago_codigo,
        dir_linea1=p.dir_linea1,
        dir_ciudad=p.dir_ciudad,
        dir_provincia=p.dir_provincia,
        dir_cp=p.dir_cp,
        dir_alias=p.dir_alias,
        detalles=detalles,
    )


def _map_detalle(d: DetallePedido) -> PedidoDetalleLinea:
    return PedidoDetalleLinea(
        nombre_producto=d.nombre_producto,
        cantidad=d.cantidad,
        precio_unitario_snapshot=d.precio_unitario_snapshot,
        subtotal=d.subtotal,
    )


def transicionar_pedido_admin(
    uow: UnitOfWork,
    pedido_id: int,
    estado_str: str,
    *,
    actor_usuario_id: int | None,
) -> Pedido:
    # valido que el string sea un estado conocido antes de pasarlo al servicio
    try:
        nuevo = EstadoPedido(estado_str)
    except ValueError as e:
        raise ValueError(f"Estado de pedido inválido: {estado_str!r}") from e
    svc = PedidoService()
    return svc.transicionar_estado(
        uow,
        pedido_id,
        nuevo,
        actor_usuario_id=actor_usuario_id,
    )


__all__ = [
    "obtener_metricas_dashboard",
    "listar_pedidos_admin",
    "obtener_pedido_admin",
    "transicionar_pedido_admin",
]
