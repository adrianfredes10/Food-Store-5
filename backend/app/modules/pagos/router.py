from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.uow.unit_of_work import UnitOfWork
from app.deps.uow import get_uow
from app.deps.auth import get_current_user
from app.deps.roles import ROL_ADMIN
from app.modules.pedidos.exceptions import PedidoNoEncontradoError
from app.modules.pagos.exceptions import (
    ErrorDominioPago,
    FormaPagoNoConfiguradaError,
    PagoNoEncontradoError,
    PedidoInvalidoParaPagoError,
    PedidoYaTienePagoAprobadoError,
    WebhookPagoInvalidoError,
)
from app.modules.pagos.schemas import PagoTarjetaRequest, PagoTarjetaResponse
from app.modules.pagos.service import CrearPagoCheckoutResult, PagoService
from app.modules.usuarios.model import Usuario

router = APIRouter(prefix="/pagos", tags=["pagos"])

_service = PagoService()


def _map_pago_error(exc: ErrorDominioPago) -> HTTPException:
    if isinstance(exc, (PagoNoEncontradoError, FormaPagoNoConfiguradaError)):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(
        exc,
        (PedidoInvalidoParaPagoError, PedidoYaTienePagoAprobadoError, WebhookPagoInvalidoError),
    ):
        return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))


def _crear_pago_tarjeta_core(
    body: PagoTarjetaRequest,
    usuario: Usuario,
    uow: UnitOfWork,
    idempotency_key: str | None,
) -> PagoTarjetaResponse:
    if usuario.id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida")
    try:
        pago = _service.crear_pago_tarjeta_desde_pedido(
            uow,
            pedido_id=body.pedido_id,
            usuario_id=usuario.id,
            token=body.token,
            payment_method_id=body.payment_method_id,
            payer_email=str(body.payer_email),
            installments=body.installments,
            idempotency_key=idempotency_key,
        )
    except PedidoNoEncontradoError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ErrorDominioPago as e:
        raise _map_pago_error(e) from e
    assert pago.id is not None
    return PagoTarjetaResponse(
        pago_id=pago.id,
        estado=pago.estado.value,
        mp_status=pago.mp_status,
        mp_payment_id=pago.mp_payment_id,
    )


@router.post("/checkout/pedidos/{pedido_id}", status_code=status.HTTP_201_CREATED)
def crear_checkout_pedido(
    pedido_id: int,
    uow: UnitOfWork = Depends(get_uow),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    """Inicia un pago para el pedido (requiere fila `forma_pago` con código MERCADOPAGO)."""
    try:
        r: CrearPagoCheckoutResult = _service.crear_pago_desde_pedido(
            uow,
            pedido_id,
            idempotency_key=idempotency_key,
        )
    except PedidoNoEncontradoError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ErrorDominioPago as e:
        raise _map_pago_error(e) from e
    return {
        "pago_id": r.pago.id,
        "external_reference": r.external_reference,
        "preference_id": r.preference_id,
        "init_point": r.init_point,
        "estado": r.pago.estado.value,
    }


@router.post("/tarjeta", response_model=PagoTarjetaResponse)
def crear_pago_tarjeta(
    body: PagoTarjetaRequest,
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> PagoTarjetaResponse:
    """Pago con token generado en el frontend (Mercado Pago SDK / CardPayment)."""
    return _crear_pago_tarjeta_core(body, usuario, uow, idempotency_key)


@router.post("/crear", response_model=PagoTarjetaResponse)
def crear_pago_spec(
    body: PagoTarjetaRequest,
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> PagoTarjetaResponse:
    """Alias especificación v5: POST /api/v1/pagos/crear (token de tarjeta vía SDK)."""
    return _crear_pago_tarjeta_core(body, usuario, uow, idempotency_key)


def _procesar_webhook(data: dict[str, Any], uow: UnitOfWork) -> dict[str, Any]:
    # proceso el webhook de mercado pago
    try:
        _service.procesar_webhook_pago(uow, data)
    except ErrorDominioPago as e:
        raise _map_pago_error(e) from e
    return {"status": "ok"}


@router.post("/webhook")
def webhook_pagos_spec(
    data: dict[str, Any],
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, str]:
    """Especificación v5: IPN MercadoPago → POST /api/v1/pagos/webhook."""
    return _procesar_webhook(data, uow)


@router.post("/webhooks/mercadopago")
def webhook_mercadopago(
    data: dict[str, Any],
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """Ruta histórica; misma lógica que /webhook."""
    return _procesar_webhook(data, uow)


@router.get("/{pedido_id}", response_model=PagoTarjetaResponse)
def obtener_pago_por_pedido(
    pedido_id: int,
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> PagoTarjetaResponse:
    """Especificación v5: GET /api/v1/pagos/{pedido_id} (dueño o ADMIN)."""
    if usuario.id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida")
    # verifico si es admin para decidir si puede ver pagos ajenos
    roles = uow.usuarios.list_codigos_roles_activos(usuario.id)
    es_admin = ROL_ADMIN in roles
    try:
        pago = _service.obtener_pago_por_pedido_para_usuario(
            uow,
            pedido_id,
            usuario.id,
            es_admin=es_admin,
        )
    except PedidoNoEncontradoError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ErrorDominioPago as e:
        raise _map_pago_error(e) from e
    assert pago.id is not None
    return PagoTarjetaResponse(
        pago_id=pago.id,
        estado=pago.estado.value,
        mp_status=pago.mp_status,
        mp_payment_id=pago.mp_payment_id,
    )
