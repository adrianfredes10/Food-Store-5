"""Servicio de pagos: checkout desde pedido, idempotencia y webhook Mercado Pago."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.enums import EstadoPago, EstadoPedido
from app.modules.pagos.exceptions import (
    FormaPagoNoConfiguradaError,
    PagoNoEncontradoError,
    PedidoInvalidoParaPagoError,
    PedidoYaTienePagoAprobadoError,
    WebhookPagoInvalidoError,
)
from app.modules.pagos.mercadopago_gateway import (
    crear_pago_con_token,
    crear_preferencia_checkout,
    obtener_pago_por_id,
)
from app.modules.pagos.model import Pago
from app.modules.pedidos.exceptions import PedidoNoEncontradoError
from app.modules.pedidos.service import PedidoService

if TYPE_CHECKING:
    from app.core.uow.unit_of_work import UnitOfWork

CODIGO_FORMA_MERCADOPAGO = "MERCADOPAGO"


@dataclass(slots=True)
class CrearPagoCheckoutResult:
    pago: Pago
    preference_id: str
    init_point: str
    external_reference: str


def _estado_pago_desde_mp_status(status: str) -> EstadoPago:
    s = (status or "").lower()
    if s == "approved":
        return EstadoPago.APROBADO
    if s in ("pending", "in_process", "authorized", "in_mediation"):
        return EstadoPago.PROCESANDO
    if s in ("refunded", "charged_back"):
        return EstadoPago.REEMBOLSADO
    return EstadoPago.RECHAZADO


def _normalizar_payload_webhook(data: dict) -> tuple[str | None, str | None, str | None]:
    """Devuelve (external_reference, payment_id, status_mp) en minúsculas si aplica."""
    if isinstance(data.get("status"), str) and (
        data.get("external_reference") is not None or data.get("payment_id") is not None
    ):
        ext = data.get("external_reference")
        pid = data.get("payment_id")
        return (
            str(ext) if ext is not None else None,
            str(pid) if pid is not None else None,
            str(data["status"]).lower(),
        )
    inner = data.get("data") or {}
    pid = inner.get("id")
    if pid is not None:
        return None, str(pid), None
    return None, None, None


def _monto_desde_payload_plano(data: dict) -> Decimal | None:
    """Lee monto del cuerpo (simulador o notificación enriquecida)."""
    for key in ("transaction_amount", "amount"):
        if key not in data:
            continue
        raw = data.get(key)
        if raw is None:
            continue
        try:
            return Decimal(str(raw))
        except (ValueError, TypeError, ArithmeticError):
            return None
    return None


def _validar_monto_antes_de_confirmar(
    pedido_total: Decimal,
    pago_monto: Decimal,
    monto_reportado: Decimal | None,
) -> None:
    """Exige coherencia entre pedido, fila `pagos` y monto del proveedor (si viene)."""
    if pago_monto != pedido_total:
        raise WebhookPagoInvalidoError(
            "el monto registrado en el pago no coincide con el total del pedido",
        )
    if monto_reportado is not None and monto_reportado != pedido_total:
        raise WebhookPagoInvalidoError(
            "el monto informado por el proveedor no coincide con el total del pedido",
        )


class PagoService:
    """Stateless: no hace commit; opera dentro del UnitOfWork del request."""

    def obtener_o_crear_por_idempotencia(
        self,
        uow: UnitOfWork,
        *,
        idempotency_key: str,
        pedido_id: int,
        forma_pago_codigo: str,
        monto: Decimal,
        external_reference: str,
        estado: EstadoPago = EstadoPago.PENDIENTE,
        proveedor_referencia_id: str | None = None,
        notas: str | None = None,
    ) -> Pago:
        existente = uow.pagos.get_by_idempotency_key(idempotency_key)
        if existente is not None:
            return existente

        nuevo = Pago(
            pedido_id=pedido_id,
            forma_pago_codigo=forma_pago_codigo,
            monto=monto,
            estado=estado,
            idempotency_key=idempotency_key,
            external_reference=external_reference,
            proveedor_referencia_id=proveedor_referencia_id,
            notas=notas,
        )

        try:
            with uow.session.begin_nested():
                uow.pagos.add(nuevo)
                uow.flush()
        except IntegrityError:
            existente = uow.pagos.get_by_idempotency_key(idempotency_key)
            if existente is not None:
                return existente
            raise

        return nuevo

    def crear_pago_desde_pedido(
        self,
        uow: UnitOfWork,
        pedido_id: int,
        *,
        idempotency_key: str | None = None,
    ) -> CrearPagoCheckoutResult:
        """Inicia cobro para un pedido PENDIENTE: registro local + preferencia MP (mock o real)."""
        # 1. verifico que el pedido exista
        pedido = uow.pedidos.get_by_id_for_update(pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(pedido_id)

        # 2. valido que esté en un estado válido para pagar
        if pedido.estado != EstadoPedido.PENDIENTE:
            raise PedidoInvalidoParaPagoError(pedido_id, "el pedido debe estar PENDIENTE")
        if pedido.total <= 0:
            raise PedidoInvalidoParaPagoError(pedido_id, "el total debe ser mayor a cero")

        # 3. me fijo que no tenga ya un pago aprobado
        if uow.pagos.tiene_pago_aprobado(pedido_id):
            raise PedidoYaTienePagoAprobadoError(pedido_id)

        pendiente = uow.pagos.get_pendiente_o_procesando_por_pedido(pedido_id)
        if pendiente is not None:
            pref_id = pendiente.proveedor_referencia_id or ""
            init = (
                f"{settings.public_app_url.rstrip('/')}/mock-mp-pay?pref={pref_id}"
                if pref_id
                else f"{settings.public_app_url.rstrip('/')}/pedido/{pedido_id}/pago/pendiente"
            )
            return CrearPagoCheckoutResult(
                pago=pendiente,
                preference_id=pref_id,
                init_point=init,
                external_reference=pendiente.external_reference,
            )

        forma = uow.pagos.get_forma_pago_por_codigo(CODIGO_FORMA_MERCADOPAGO)
        if forma is None:
            raise FormaPagoNoConfiguradaError(CODIGO_FORMA_MERCADOPAGO)

        key = idempotency_key or str(uuid.uuid4())
        external_reference = str(pedido_id)
        monto = pedido.total

        pago = self.obtener_o_crear_por_idempotencia(
            uow,
            idempotency_key=key,
            pedido_id=pedido_id,
            forma_pago_codigo=forma.codigo,
            monto=monto,
            external_reference=external_reference,
            estado=EstadoPago.PENDIENTE,
        )

        # 4. armo la preferencia en mercado pago y guardo el id
        notification_url = f"{settings.public_app_url.rstrip('/')}/api/v1/pagos/webhook"
        pref = crear_preferencia_checkout(
            titulo=f"Pedido #{pedido_id}",
            monto=monto,
            moneda=pedido.moneda,
            external_reference=external_reference,
            notification_url=notification_url,
        )
        pago.proveedor_referencia_id = pref.preference_id
        uow.flush()

        return CrearPagoCheckoutResult(
            pago=pago,
            preference_id=pref.preference_id,
            init_point=pref.init_point,
            external_reference=external_reference,
        )

    def procesar_webhook_pago(self, uow: UnitOfWork, data: dict) -> Pago:
        """Procesa notificación del proveedor: actualiza pago y, si aprobado, confirma el pedido."""
        # 1. normalizo el payload que manda mercado pago
        ext_ref, payment_id, status_mp = _normalizar_payload_webhook(data)
        monto_reportado = _monto_desde_payload_plano(data)

        if payment_id:
            if status_mp is None:
                try:
                    info = obtener_pago_por_id(payment_id)
                except RuntimeError as e:
                    raise WebhookPagoInvalidoError(str(e)) from e
                status_mp = info.status.lower()
                if ext_ref is None and info.external_reference is not None:
                    ext_ref = info.external_reference
                if monto_reportado is None and info.transaction_amount is not None:
                    monto_reportado = info.transaction_amount
            elif status_mp == "approved" and monto_reportado is None:
                try:
                    info_amt = obtener_pago_por_id(payment_id)
                    if info_amt.transaction_amount is not None:
                        monto_reportado = info_amt.transaction_amount
                except RuntimeError as e:
                    raise WebhookPagoInvalidoError(str(e)) from e

        if status_mp is None:
            raise WebhookPagoInvalidoError("no se pudo determinar el estado del pago")

        # 2. si ya fue procesado, lo ignoro (idempotencia)
        if payment_id and ext_ref:
            ya_procesado = uow.pagos.get_by_mp_payment_id(payment_id)
            if (
                ya_procesado is not None
                and (ya_procesado.mp_status or "").lower() == status_mp
                and ya_procesado.external_reference == ext_ref
            ):
                return ya_procesado

        # 3. busco el pago en la base de datos
        pago_row: Pago | None = None
        if payment_id:
            pago_row = uow.pagos.get_by_mp_payment_id(payment_id)
        if pago_row is None and ext_ref is not None:
            pago_row = uow.pagos.get_pendiente_o_procesando_por_external_reference(ext_ref)

        if pago_row is None:
            raise PagoNoEncontradoError(
                f"external_reference={ext_ref!r}, payment_id={payment_id!r}",
            )

        pago = uow.pagos.get_by_id_for_update(pago_row.id)
        if pago is None:
            raise PagoNoEncontradoError(f"id={pago_row.id}")

        if payment_id:
            pago.mp_payment_id = payment_id

        # 4. aplico el nuevo estado al pago
        nuevo_estado = _estado_pago_desde_mp_status(status_mp)
        if (
            (pago.mp_status or "") == status_mp
            and pago.estado == nuevo_estado
            and (not payment_id or pago.mp_payment_id == payment_id)
        ):
            return pago

        debe_confirmar_pedido = False
        if status_mp == "approved":
            pedido = uow.pedidos.get_by_id_for_update(pago.pedido_id)
            if pedido is None:
                raise WebhookPagoInvalidoError("pedido asociado al pago no existe")
            if pedido.estado == EstadoPedido.PENDIENTE:
                _validar_monto_antes_de_confirmar(pedido.total, pago.monto, monto_reportado)
                debe_confirmar_pedido = True
            # Si el pedido ya no está PENDIENTE: no confirmar (idempotente / evita doble confirmación).

        # 5. guardo los cambios
        pago.mp_status = status_mp
        pago.estado = nuevo_estado
        uow.flush()

        if status_mp == "approved" and debe_confirmar_pedido:
            pedido_svc = PedidoService()
            pedido_svc.transicionar_estado(uow, pago.pedido_id, EstadoPedido.CONFIRMADO)

        return pago

    def crear_pago_tarjeta_desde_pedido(
        self,
        uow: UnitOfWork,
        *,
        pedido_id: int,
        usuario_id: int,
        token: str,
        payment_method_id: str,
        payer_email: str,
        installments: int = 1,
        idempotency_key: str | None = None,
    ) -> Pago:
        """Cobra con token del SDK (tarjeta). Idempotente por ``Idempotency-Key``."""
        # 1. verifico que el pedido exista y sea del usuario
        pedido = uow.pedidos.get_by_id_for_update(pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(pedido_id)
        if pedido.usuario_id != usuario_id:
            raise PedidoInvalidoParaPagoError(pedido_id, "no autorizado")

        # 2. valido el estado del pedido antes de cobrar
        if pedido.estado != EstadoPedido.PENDIENTE:
            raise PedidoInvalidoParaPagoError(pedido_id, "el pedido debe estar PENDIENTE")
        if pedido.total <= 0:
            raise PedidoInvalidoParaPagoError(pedido_id, "el total debe ser mayor a cero")

        # esto es para que no se pueda pagar dos veces
        ya_procesado = uow.pagos.tiene_pago_aprobado(pedido_id)
        if ya_procesado:
            raise PedidoYaTienePagoAprobadoError(pedido_id)

        key = (idempotency_key or "").strip() or str(uuid.uuid4())
        pendiente = uow.pagos.get_pendiente_o_procesando_por_pedido(pedido_id)
        if pendiente is not None and pendiente.idempotency_key != key:
            if pendiente.proveedor_referencia_id:
                raise PedidoInvalidoParaPagoError(
                    pedido_id,
                    "ya existe un checkout Pro pendiente para este pedido",
                )
            raise PedidoInvalidoParaPagoError(
                pedido_id,
                "ya existe un intento de pago pendiente; reutilizá el mismo Idempotency-Key",
            )

        forma = uow.pagos.get_forma_pago_por_codigo(CODIGO_FORMA_MERCADOPAGO)
        if forma is None:
            raise FormaPagoNoConfiguradaError(CODIGO_FORMA_MERCADOPAGO)

        external_reference = str(pedido_id)
        pago = self.obtener_o_crear_por_idempotencia(
            uow,
            idempotency_key=key,
            pedido_id=pedido_id,
            forma_pago_codigo=forma.codigo,
            monto=pedido.total,
            external_reference=external_reference,
            estado=EstadoPago.PENDIENTE,
        )
        if pago.pedido_id != pedido_id:
            raise PedidoInvalidoParaPagoError(pedido_id, "clave de idempotencia inconsistente")

        # 3. si ya tiene payment_id de mp, lo devuelvo directo (idempotencia)
        if pago.mp_payment_id:
            return pago

        # 4. llamo a la api de mercado pago con el token del frontend
        try:
            info = crear_pago_con_token(
                token=token,
                transaction_amount=pedido.total,
                description=f"Pedido #{pedido_id}",
                external_reference=external_reference,
                payment_method_id=payment_method_id,
                payer_email=payer_email,
                installments=installments,
                idempotency_key=key,
            )
        except RuntimeError as e:
            raise WebhookPagoInvalidoError(str(e)) from e

        assert pago.id is not None
        pago_locked = uow.pagos.get_by_id_for_update(pago.id)
        if pago_locked is None:
            raise PagoNoEncontradoError(f"id={pago.id}")

        pago_locked.mp_payment_id = info.payment_id
        pago_locked.mp_status = info.status
        pago_locked.estado = _estado_pago_desde_mp_status(info.status)
        uow.flush()

        if info.status == "approved":
            pedido_locked = uow.pedidos.get_by_id_for_update(pago_locked.pedido_id)
            if pedido_locked is None:
                raise WebhookPagoInvalidoError("pedido asociado al pago no existe")
            if pedido_locked.estado == EstadoPedido.PENDIENTE:
                _validar_monto_antes_de_confirmar(
                    pedido_locked.total,
                    pago_locked.monto,
                    info.transaction_amount,
                )
                pedido_svc = PedidoService()
                pedido_svc.transicionar_estado(uow, pedido_locked.id, EstadoPedido.CONFIRMADO)  # type: ignore[arg-type]

        return pago_locked

    def obtener_pago_por_pedido_para_usuario(
        self,
        uow: UnitOfWork,
        pedido_id: int,
        usuario_id: int,
        *,
        es_admin: bool,
    ) -> Pago:
        pedido = uow.pedidos.get_by_id(pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(pedido_id)
        if not es_admin and pedido.usuario_id != usuario_id:
            raise PedidoNoEncontradoError(pedido_id)
        pago = uow.pagos.get_mas_reciente_por_pedido(pedido_id)
        if pago is None:
            raise PagoNoEncontradoError(f"pedido_id={pedido_id}")
        return pago
