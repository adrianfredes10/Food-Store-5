from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.uow.unit_of_work import UnitOfWork
from app.deps.uow import get_uow
from app.deps.roles import require_admin
from app.modules.admin import service as admin_service
from app.modules.admin.schemas import (
    AdminPedidosPage,
    AdminPedidoTransicionRequest,
    MetricasDashboardResponse,
    PedidoAdminDetalleResponse,
)
from app.modules.pedidos.exceptions import ErrorDominioPedido, PedidoNoEncontradoError
from app.modules.usuarios.model import Usuario

router = APIRouter(prefix="/admin", tags=["admin"])


def _map_pedido_domain(exc: ErrorDominioPedido) -> HTTPException:
    return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/dashboard", response_model=MetricasDashboardResponse)
def admin_dashboard(
    _: Usuario = Depends(require_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> MetricasDashboardResponse:
    return admin_service.obtener_metricas_dashboard(uow)


@router.get("/pedidos", response_model=AdminPedidosPage)
def admin_listar_pedidos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _: Usuario = Depends(require_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> AdminPedidosPage:
    return admin_service.listar_pedidos_admin(uow, page=page, size=size)


@router.get("/pedidos/{pedido_id}", response_model=PedidoAdminDetalleResponse)
def admin_obtener_pedido(
    pedido_id: int,
    _: Usuario = Depends(require_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> PedidoAdminDetalleResponse:
    try:
        return admin_service.obtener_pedido_admin(uow, pedido_id)
    except PedidoNoEncontradoError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/pedidos/{pedido_id}/transicion", response_model=PedidoAdminDetalleResponse)
def admin_transicion_pedido(
    pedido_id: int,
    body: AdminPedidoTransicionRequest,
    usuario: Usuario = Depends(require_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> PedidoAdminDetalleResponse:
    # aplico la transición de estado y después devuelvo el pedido actualizado
    try:
        admin_service.transicionar_pedido_admin(
            uow,
            pedido_id,
            body.estado.strip(),
            actor_usuario_id=usuario.id,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ErrorDominioPedido as e:
        raise _map_pedido_domain(e) from e
    try:
        return admin_service.obtener_pedido_admin(uow, pedido_id)
    except PedidoNoEncontradoError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
