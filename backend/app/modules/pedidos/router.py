from fastapi import APIRouter, Depends, HTTPException, Query, status, Body

from app.core.enums import EstadoPedido
from app.core.uow.unit_of_work import UnitOfWork
from app.deps.uow import get_uow
from app.deps.auth import get_current_user
from app.deps.roles import ROL_ADMIN, ROL_PEDIDOS
from app.modules.pedidos.exceptions import ErrorDominioPedido, PedidoNoEncontradoError
from app.modules.pedidos.schemas import (
    CancelarPedidoRequest,
    CrearPedidoRequest,
    HistorialEstadoPedidoRead,
    PaginaPedidosCliente,
    PedidoCreadoResponse,
    PedidoDetalleCliente,
    PedidoResumenResponse,
)
from app.modules.pedidos.service import PedidoService
from app.modules.usuarios.model import Usuario

router = APIRouter(prefix="/pedidos", tags=["pedidos"])

_pedido_service = PedidoService()


def _map_pedido_error(exc: ErrorDominioPedido) -> HTTPException:
    # si no existe mando 404, sino 400
    if isinstance(exc, PedidoNoEncontradoError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))


def _roles_staff(uow: UnitOfWork, usuario_id: int) -> bool:
    roles = uow.usuarios.list_codigos_roles_activos(usuario_id)
    return ROL_ADMIN in roles or ROL_PEDIDOS in roles


@router.get("", response_model=PaginaPedidosCliente)
def listar_mis_pedidos(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    estado: EstadoPedido | None = Query(None),
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PaginaPedidosCliente:
    # traigo todos con paginacion
    if usuario.id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida")
    return _pedido_service.listar_pedidos_cliente(
        uow,
        usuario.id,
        page=page,
        size=size,
        estado=estado,
    )


@router.get("/{pedido_id}/historial", response_model=list[HistorialEstadoPedidoRead])
def obtener_historial_pedido(
    pedido_id: int,
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[HistorialEstadoPedidoRead]:
    if usuario.id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida")
    staff = _roles_staff(uow, usuario.id)
    try:
        return _pedido_service.obtener_historial(
            uow,
            pedido_id,
            usuario.id,
            es_admin_o_pedidos=staff,
        )
    except ErrorDominioPedido as e:
        raise _map_pedido_error(e) from e


@router.delete("/{pedido_id}", response_model=PedidoDetalleCliente)
def cancelar_pedido_delete(
    pedido_id: int,
    body: CancelarPedidoRequest = Body(...),
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PedidoDetalleCliente:
    # si no existe mando 404
    if usuario.id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida")
    try:
        return _pedido_service.cancelar_pedido_cliente(
            uow,
            pedido_id,
            usuario.id,
            body.motivo,
        )
    except ErrorDominioPedido as e:
        raise _map_pedido_error(e) from e


@router.get("/{pedido_id}", response_model=PedidoDetalleCliente)
def obtener_pedido(
    pedido_id: int,
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PedidoDetalleCliente:
    # si no existe mando 404
    if usuario.id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida")
    staff = _roles_staff(uow, usuario.id)
    try:
        return _pedido_service.obtener_pedido_detalle(
            uow,
            pedido_id,
            usuario.id,
            es_admin_o_pedidos=staff,
        )
    except ErrorDominioPedido as e:
        raise _map_pedido_error(e) from e


@router.post("", response_model=PedidoCreadoResponse, status_code=status.HTTP_201_CREATED)
def crear_pedido(
    body: CrearPedidoRequest,
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PedidoCreadoResponse:
    if usuario.id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida")
    uid = usuario.id
    lineas = [(i.producto_id, i.cantidad, i.personalizacion) for i in body.items]
    try:
        pedido = _pedido_service.crear_pedido(
            uow,
            usuario_id=uid,
            lineas=lineas,
            direccion_entrega_id=body.direccion_entrega_id,
            observaciones_cliente=body.observaciones_cliente,
            forma_pago_codigo=body.forma_pago_codigo,
            actor_usuario_id=uid,
        )
    except ErrorDominioPedido as e:
        raise _map_pedido_error(e) from e
    assert pedido.id is not None
    return PedidoCreadoResponse(
        id=pedido.id,
        estado=pedido.estado.value,
        total=pedido.total,
        moneda=pedido.moneda,
        costo_envio=pedido.costo_envio,
        forma_pago_codigo=pedido.forma_pago_codigo,
        dir_linea1=pedido.dir_linea1,
        dir_ciudad=pedido.dir_ciudad,
        dir_provincia=pedido.dir_provincia,
        dir_cp=pedido.dir_cp,
        dir_alias=pedido.dir_alias,
    )


@router.post("/{pedido_id}/cancelar", response_model=PedidoResumenResponse)
def cancelar_pedido_post(
    pedido_id: int,
    body: CancelarPedidoRequest,
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PedidoResumenResponse:
    """Compatibilidad: mismo criterio que DELETE (solo PENDIENTE, due?o del pedido)."""
    if usuario.id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida")
    try:
        _pedido_service.cancelar_pedido_cliente(
            uow,
            pedido_id,
            usuario.id,
            body.motivo,
        )
    except ErrorDominioPedido as e:
        raise _map_pedido_error(e) from e
    actualizado = uow.pedidos.get_by_id(pedido_id)
    if actualizado is None or actualizado.id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    return PedidoResumenResponse(
        id=actualizado.id,
        estado=actualizado.estado.value,
        total=actualizado.total,
        moneda=actualizado.moneda,
        direccion_entrega_id=actualizado.direccion_entrega_id,
        costo_envio=actualizado.costo_envio,
        forma_pago_codigo=actualizado.forma_pago_codigo,
        dir_linea1=actualizado.dir_linea1,
        dir_ciudad=actualizado.dir_ciudad,
        dir_provincia=actualizado.dir_provincia,
        dir_cp=actualizado.dir_cp,
        dir_alias=actualizado.dir_alias,
    )
