"""Servicio de pedidos: FSM de estados, creación con validación y stock bajo concurrencia."""

from __future__ import annotations

import math
from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING, Sequence

from app.core.enums import EstadoPedido
from app.modules.pedidos.exceptions import (
    DireccionEntregaNoValidaError,
    ErrorDominioPedido,
    FormaPagoNoValidaError,
    MotivoCancelacionRequeridoError,
    PedidoEnEstadoTerminalError,
    PedidoHistorialDesincronizadoError,
    PedidoNoEncontradoError,
    PedidoSinItemsError,
    ProductoNoComprableEnPedidoError,
    TransicionPedidoInvalidaError,
)
from app.modules.pedidos.model import DetallePedido, HistorialEstadoPedido, Pedido
from app.modules.pedidos.schemas import (
    DetallePedidoRead,
    HistorialEstadoPedidoRead,
    PaginaPedidosCliente,
    PedidoDetalleCliente,
    PedidoListadoItem,
)
from app.modules.productos.model import Producto

if TYPE_CHECKING:
    from app.core.uow.unit_of_work import UnitOfWork

_TRANSICIONES_PERMITIDAS: dict[EstadoPedido, frozenset[EstadoPedido]] = {
    EstadoPedido.PENDIENTE: frozenset({EstadoPedido.CONFIRMADO, EstadoPedido.CANCELADO}),
    EstadoPedido.CONFIRMADO: frozenset({EstadoPedido.EN_PREP, EstadoPedido.CANCELADO}),
    EstadoPedido.EN_PREP: frozenset({EstadoPedido.EN_CAMINO, EstadoPedido.CANCELADO}),
    EstadoPedido.EN_CAMINO: frozenset({EstadoPedido.ENTREGADO}),
    EstadoPedido.ENTREGADO: frozenset(),
    EstadoPedido.CANCELADO: frozenset(),
}

_ESTADOS_TERMINALES = frozenset({EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO})

COSTO_ENVIO_FIJO_V1 = Decimal("50.00")


def _validar_coherencia_pedido_con_historial(pedido_id: int, pedido: Pedido, ultimo: HistorialEstadoPedido | None) -> None:
    """Exige que el último estado_nuevo del historial coincida con pedido.estado (invariante append-only)."""
    estado_actual = pedido.estado.value
    if ultimo is None:
        if pedido.estado != EstadoPedido.PENDIENTE:
            raise PedidoHistorialDesincronizadoError(pedido_id, estado_actual, None)
        return
    if ultimo.estado_nuevo != estado_actual:
        raise PedidoHistorialDesincronizadoError(pedido_id, estado_actual, ultimo.estado_nuevo)


def _agrupar_cantidad_por_producto(lineas: Sequence[tuple[int, int, list[int] | None]]) -> dict[int, int]:
    agrupado: dict[int, int] = defaultdict(int)
    for producto_id, cantidad, _pers in lineas:
        if cantidad < 1:
            raise ProductoNoComprableEnPedidoError(producto_id, "la cantidad debe ser mayor a cero")
        agrupado[producto_id] += cantidad
    return dict(agrupado)


def _validar_estado_producto_para_linea(producto_id: int, cantidad_total: int, p: Producto) -> None:
    """Comprueba reglas de negocio de pedidos sobre la fila de producto (sin pasar por el servicio de catálogo)."""
    if cantidad_total < 1:
        raise ProductoNoComprableEnPedidoError(producto_id, "la cantidad debe ser mayor a cero")
    if p.stock_cantidad < 0:
        raise ProductoNoComprableEnPedidoError(producto_id, "stock inválido en catálogo")
    if p.deleted_at is not None:
        raise ProductoNoComprableEnPedidoError(producto_id, "eliminado")
    if not p.disponible:
        raise ProductoNoComprableEnPedidoError(producto_id, "no disponible")
    if p.stock_cantidad < cantidad_total:
        raise ProductoNoComprableEnPedidoError(producto_id, "sin stock suficiente")


def _revalidar_y_bloquear_productos_para_crear(
    uow: UnitOfWork,
    cantidad_por_producto: dict[int, int],
) -> dict[int, Producto]:
    """Revalida stock/disponibilidad tras bloquear cada producto con ``FOR UPDATE``.

    Los ``producto_id`` se bloquean **siempre en orden ascendente** (lista determinista,
    independiente del orden de las líneas del pedido). Así dos transacciones que tocan
    el mismo subconjunto de productos adquieren locks en el mismo orden y se reduce el
    riesgo de deadlock. Misma convención que ``_descontar_stock_al_confirmar``.
    """
    bloqueados: dict[int, Producto] = {}
    producto_ids_en_orden_de_lock = sorted(cantidad_por_producto.keys())
    for producto_id in producto_ids_en_orden_de_lock:
        p = uow.productos.get_by_id_for_update(producto_id)
        if p is None:
            raise ProductoNoComprableEnPedidoError(producto_id, "no existe o fue eliminado")
        _validar_estado_producto_para_linea(producto_id, cantidad_por_producto[producto_id], p)
        bloqueados[producto_id] = p
    return bloqueados


def _descontar_stock_al_confirmar(uow: UnitOfWork, pedido_id: int) -> None:
    # aca descuento el stock de cada producto del pedido
    detalles = uow.pedidos.list_detalles_por_pedido_id(pedido_id)
    necesario: dict[int, int] = defaultdict(int)
    for d in detalles:
        if d.producto_id is None:
            continue
        necesario[d.producto_id] += d.cantidad
    producto_ids_en_orden_de_lock = sorted(necesario.keys())
    for producto_id in producto_ids_en_orden_de_lock:
        cant = necesario[producto_id]
        p = uow.productos.get_by_id_for_update(producto_id)
        if p is None:
            raise ProductoNoComprableEnPedidoError(producto_id, "no disponible o eliminado")
        _validar_estado_producto_para_linea(producto_id, cant, p)
        p.stock_cantidad -= cant
        if p.stock_cantidad == 0:
            p.disponible = False


class PedidoService:
    """Stateless: recibe UnitOfWork en cada operación; no hace commit."""

    def crear_pedido(
        self,
        uow: UnitOfWork,
        *,
        usuario_id: int,
        lineas: Sequence[tuple[int, int, list[int] | None]],
        direccion_entrega_id: int | None = None,
        observaciones_cliente: str | None = None,
        moneda: str = "ARS",
        forma_pago_codigo: str = "MERCADOPAGO",
        actor_usuario_id: int | None = None,
    ) -> Pedido:
        """Crea pedido PENDIENTE con detalles. Valida líneas y, bajo bloqueo, vuelve a comprobar stock.

        No descuenta stock aquí (solo al confirmar vía ``transicionar_estado``). El llamador no debe
        invocar ``validar_lineas_para_crear_pedido`` por separado: ya está incluido.
        """
        # 1. verifico la direccion si viene
        dir_linea1 = dir_linea2 = dir_ciudad = dir_provincia = dir_cp = dir_alias = None
        if direccion_entrega_id is not None:
            d = uow.direcciones.get_by_id(direccion_entrega_id)
            if d is None or d.usuario_id != usuario_id or not d.activo:
                raise DireccionEntregaNoValidaError(direccion_entrega_id)
            dir_linea1 = d.linea1
            dir_alias = d.alias

        # 2. valido forma de pago
        if uow.pagos.get_forma_pago_por_codigo(forma_pago_codigo) is None:
            raise FormaPagoNoValidaError(forma_pago_codigo)

        # 3. valido y bloqueo los productos
        self.validar_lineas_para_crear_pedido(uow, lineas)
        cantidad_por_producto = _agrupar_cantidad_por_producto(lineas)
        productos = _revalidar_y_bloquear_productos_para_crear(uow, cantidad_por_producto)

        subtotal_items: Decimal = Decimal("0")
        for producto_id, cantidad, _pers in lineas:
            p = productos[producto_id]
            cant_dec = Decimal(cantidad)
            subtotal_items += p.precio * cant_dec

        total = subtotal_items + COSTO_ENVIO_FIJO_V1

        # 4. guardo el pedido
        pedido = Pedido(
            usuario_id=usuario_id,
            direccion_entrega_id=direccion_entrega_id,
            estado=EstadoPedido.PENDIENTE,
            total=total,
            moneda=moneda,
            observaciones_cliente=observaciones_cliente,
            costo_envio=COSTO_ENVIO_FIJO_V1,
            forma_pago_codigo=forma_pago_codigo,
            dir_linea1=dir_linea1,
            dir_linea2=dir_linea2,
            dir_ciudad=dir_ciudad,
            dir_provincia=dir_provincia,
            dir_cp=dir_cp,
            dir_alias=dir_alias,
        )
        uow.pedidos.add(pedido)
        uow.flush()
        assert pedido.id is not None

        reg = HistorialEstadoPedido(
            pedido_id=pedido.id,
            estado_anterior=None,
            estado_nuevo=EstadoPedido.PENDIENTE.value,
            usuario_id=actor_usuario_id,
        )
        uow.historial_estado_pedido.add(reg)

        for producto_id, cantidad, personalizacion in lineas:
            p = productos[producto_id]
            cant_dec = Decimal(cantidad)
            subtotal = p.precio * cant_dec
            detalle = DetallePedido(
                pedido_id=pedido.id,
                producto_id=producto_id,
                nombre_producto=p.nombre,
                precio_unitario_snapshot=p.precio,
                cantidad=cantidad,
                subtotal=subtotal,
                personalizacion=personalizacion,
            )
            uow.pedidos.add_detalle(detalle)

        uow.flush()
        return pedido

    def validar_lineas_para_crear_pedido(self, uow: UnitOfWork, lineas: Sequence[tuple[int, int, list[int] | None]]) -> None:
        """Antes de persistir un pedido: comprueba cada producto (no eliminado, disponible, stock).

        Cada tupla es ``(producto_id, cantidad, personalizacion)``. Varias líneas del mismo producto suman cantidad.
        Lee el estado actual vía repositorio; no delega en ``ProductoCatalogoService``.
        """
        if len(lineas) == 0:
            raise PedidoSinItemsError()
        for producto_id, cantidad_total in _agrupar_cantidad_por_producto(lineas).items():
            p = uow.productos.get_by_id(producto_id, incluir_eliminados=True)
            if p is None:
                raise ProductoNoComprableEnPedidoError(producto_id, "no existe")
            _validar_estado_producto_para_linea(producto_id, cantidad_total, p)

    def transicionar_estado(
        self,
        uow: UnitOfWork,
        pedido_id: int,
        nuevo_estado: EstadoPedido,
        *,
        motivo: str | None = None,
        actor_usuario_id: int | None = None,
    ) -> Pedido:
        pedido = uow.pedidos.get_by_id_for_update(pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(pedido_id)

        # verifico que el historial este sincronizado
        ultimo = uow.historial_estado_pedido.get_ultimo_por_pedido_id(pedido_id)
        _validar_coherencia_pedido_con_historial(pedido_id, pedido, ultimo)

        actual = pedido.estado
        if actual in _ESTADOS_TERMINALES:
            raise PedidoEnEstadoTerminalError(pedido_id, actual)

        permitidos = _TRANSICIONES_PERMITIDAS.get(actual, frozenset())
        if nuevo_estado not in permitidos:
            raise TransicionPedidoInvalidaError(pedido_id, actual, nuevo_estado)

        if nuevo_estado == EstadoPedido.CANCELADO:
            if motivo is None or not motivo.strip():
                raise MotivoCancelacionRequeridoError(pedido_id)
            pedido.motivo_cancelacion = motivo.strip()

        if actual == EstadoPedido.PENDIENTE and nuevo_estado == EstadoPedido.CONFIRMADO:
            _descontar_stock_al_confirmar(uow, pedido_id)

        registro = HistorialEstadoPedido(
            pedido_id=pedido.id,
            estado_anterior=actual.value,
            estado_nuevo=nuevo_estado.value,
            motivo=motivo.strip() if nuevo_estado == EstadoPedido.CANCELADO and motivo else None,
            usuario_id=actor_usuario_id,
        )
        uow.historial_estado_pedido.add(registro)

        pedido.estado = nuevo_estado
        return pedido

    def _armar_pedido_detalle_cliente(self, uow: UnitOfWork, pedido: Pedido) -> PedidoDetalleCliente:
        assert pedido.id is not None
        detalles_orm = uow.pedidos.list_detalles_por_pedido_id(pedido.id)
        detalles = [DetallePedidoRead.model_validate(d) for d in detalles_orm]
        return PedidoDetalleCliente(
            id=pedido.id,
            estado=pedido.estado.value,
            total=pedido.total,
            costo_envio=pedido.costo_envio,
            forma_pago_codigo=pedido.forma_pago_codigo,
            dir_linea1=pedido.dir_linea1,
            dir_alias=pedido.dir_alias,
            observaciones_cliente=pedido.observaciones_cliente,
            created_at=pedido.created_at,
            detalles=detalles,
        )

    def listar_pedidos_cliente(
        self,
        uow: UnitOfWork,
        usuario_id: int,
        page: int,
        size: int,
        estado: EstadoPedido | None,
    ) -> PaginaPedidosCliente:
        # traigo todos con paginacion
        page = max(1, page)
        size = min(50, max(1, size))
        pedidos, total = uow.pedidos.listar_por_usuario(usuario_id, page=page, size=size, estado=estado)
        pages = math.ceil(total / size) if total else 0
        items = [
            PedidoListadoItem(
                id=p.id,
                estado=p.estado.value,
                total=p.total,
                costo_envio=p.costo_envio,
                created_at=p.created_at,
                cantidad_items=len(p.detalles),
            )
            for p in pedidos
            if p.id is not None
        ]
        return PaginaPedidosCliente(items=items, total=total, page=page, size=size, pages=pages)

    def obtener_pedido_detalle(
        self,
        uow: UnitOfWork,
        pedido_id: int,
        usuario_id: int,
        *,
        es_admin_o_pedidos: bool,
    ) -> PedidoDetalleCliente:
        # si no existe mando 404
        if es_admin_o_pedidos:
            pedido = uow.pedidos.get_by_id(pedido_id)
        else:
            pedido = uow.pedidos.get_by_id_y_usuario(pedido_id, usuario_id)
        if pedido is None:
            raise PedidoNoEncontradoError(pedido_id)
        return self._armar_pedido_detalle_cliente(uow, pedido)

    def obtener_historial(
        self,
        uow: UnitOfWork,
        pedido_id: int,
        usuario_id: int,
        *,
        es_admin_o_pedidos: bool,
    ) -> list[HistorialEstadoPedidoRead]:
        if es_admin_o_pedidos:
            if uow.pedidos.get_by_id(pedido_id) is None:
                raise PedidoNoEncontradoError(pedido_id)
        else:
            if uow.pedidos.get_by_id_y_usuario(pedido_id, usuario_id) is None:
                raise PedidoNoEncontradoError(pedido_id)
        rows = uow.pedidos.listar_historial(pedido_id)
        return [HistorialEstadoPedidoRead.model_validate(r) for r in rows]

    def cancelar_pedido_cliente(
        self,
        uow: UnitOfWork,
        pedido_id: int,
        usuario_id: int,
        motivo: str,
    ) -> PedidoDetalleCliente:
        # si no existe mando 404
        pedido = uow.pedidos.get_by_id_y_usuario(pedido_id, usuario_id)
        if pedido is None:
            raise PedidoNoEncontradoError(pedido_id)
        if pedido.estado != EstadoPedido.PENDIENTE:
            raise ErrorDominioPedido(
                f"Solo se pueden cancelar pedidos en estado PENDIENTE. "
                f"El pedido {pedido_id} está en estado {pedido.estado.value}.",
            )
        actualizado = self.transicionar_estado(
            uow,
            pedido_id,
            EstadoPedido.CANCELADO,
            motivo=motivo,
            actor_usuario_id=usuario_id,
        )
        return self._armar_pedido_detalle_cliente(uow, actualizado)
