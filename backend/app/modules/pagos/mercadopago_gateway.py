"""Cliente Mercado Pago: preferencias de checkout y consulta de pagos (mock o API real)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


"""
TESTING MANUAL DEL FLUJO COMPLETO:
1. Requisitos:
   - Backend: uvicorn app.main:app --reload --host 127.0.0.1 --port 8008
   - Frontend: npm run dev
   - Tunnel: cloudflared tunnel --url http://127.0.0.1:8008
   - .env: 
     MERCADOPAGO_MOCK=false
     PUBLIC_APP_URL=https://sept-trance-accuracy-repository.trycloudflare.com

2. Pasos:
   a. Login en el frontend.
   b. Crear pedido -> Redirige a /pedido/{id}.
   c. Click 'Pagar ahora' -> Redirige a Mercado Pago Sandbox.
   d. Usar tarjeta de prueba (Nombre: APRO, Número: 4509...).
   e. Al terminar, MP redirige a /pedido/{id}?status=approved.
   f. El Webhook llega a /api/v1/pagos/webhook.
   g. El pedido cambia a CONFIRMADO automáticamente.

3. Verificar Webhook:
   curl -X POST https://sept-trance-accuracy-repository.trycloudflare.com/api/v1/pagos/webhook \
    -H "Content-Type: application/json" -d '{"test": true}'
   Respuesta esperada: {"status": "ok"}
"""


@dataclass(frozen=True, slots=True)
class PreferenciaCreada:
    preference_id: str
    init_point: str


@dataclass(frozen=True, slots=True)
class PagoProveedorInfo:
    payment_id: str
    status: str
    external_reference: str | None
    transaction_amount: Decimal | None = None


def _mp_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.mercadopago_access_token}",
        "Content-Type": "application/json",
    }


def crear_preferencia_checkout(
    *,
    titulo: str,
    monto: Decimal,
    moneda: str,
    external_reference: str,
    notification_url: str,
) -> PreferenciaCreada:
    """Crea una preferencia de Checkout Pro. En mock devuelve URLs ficticias."""
    if settings.mercadopago_mock:
        pref_id = f"MOCK-PREF-{uuid.uuid4().hex[:12]}"
        return PreferenciaCreada(
            preference_id=pref_id,
            init_point=f"{settings.public_app_url.rstrip('/')}/mock-mp-pay?pref={pref_id}",
        )

    if not settings.mercadopago_access_token:
        raise RuntimeError("mercadopago_access_token requerido cuando mercadopago_mock=False")

    payload: dict[str, Any] = {
        "items": [
            {
                "title": titulo[:256],
                "quantity": 1,
                "currency_id": moneda,
                "unit_price": float(monto),
            },
        ],
        "external_reference": external_reference,
        "notification_url": notification_url,
        "back_urls": {
            "success": f"{settings.public_app_url.rstrip('/')}/pedido/{external_reference}?status=approved",
            "failure": f"{settings.public_app_url.rstrip('/')}/pedido/{external_reference}?status=rejected",
            "pending": f"{settings.public_app_url.rstrip('/')}/pedido/{external_reference}?status=pending",
        },
        "auto_return": "approved",
    }
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        "https://api.mercadopago.com/checkout/preferences",
        data=body,
        headers=_mp_headers(),
        method="POST",
    )
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Error creando preferencia Mercado Pago: {e}") from e

    pref_id = str(data.get("id", ""))
    init_point = str(data.get("init_point") or data.get("sandbox_init_point") or "")
    if not pref_id or not init_point:
        raise RuntimeError("Respuesta de Mercado Pago sin id o init_point")
    return PreferenciaCreada(preference_id=pref_id, init_point=init_point)


def obtener_pago_por_id(payment_id: str) -> PagoProveedorInfo:
    """Consulta GET /v1/payments/{id}. En mock solo admite devolver datos si el id tiene prefijo MOCK-."""
    if settings.mercadopago_mock:
        return PagoProveedorInfo(
            payment_id=payment_id,
            status="approved",
            external_reference=None,
            transaction_amount=None,
        )

    if not settings.mercadopago_access_token:
        raise RuntimeError("mercadopago_access_token requerido cuando mercadopago_mock=False")

    req = Request(
        f"https://api.mercadopago.com/v1/payments/{payment_id}",
        headers={"Authorization": f"Bearer {settings.mercadopago_access_token}"},
        method="GET",
    )
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Error consultando pago Mercado Pago: {e}") from e

    raw_amt = data.get("transaction_amount")
    tx_amt: Decimal | None = None
    if raw_amt is not None:
        try:
            tx_amt = Decimal(str(raw_amt))
        except (ValueError, TypeError, ArithmeticError):
            tx_amt = None

    return PagoProveedorInfo(
        payment_id=str(data.get("id", payment_id)),
        status=str(data.get("status", "") or "").lower(),
        external_reference=str(data["external_reference"])
        if data.get("external_reference") is not None
        else None,
        transaction_amount=tx_amt,
    )


def crear_pago_con_token(
    *,
    token: str,
    transaction_amount: Decimal,
    description: str,
    external_reference: str,
    payment_method_id: str,
    payer_email: str,
    installments: int = 1,
    idempotency_key: str | None = None,
) -> PagoProveedorInfo:
    """POST /v1/payments con token de tarjeta (SDK). En mock aprueba sin llamar a la API."""
    if settings.mercadopago_mock:
        pay_id = f"MOCK-PAY-{uuid.uuid4().hex[:12]}"
        return PagoProveedorInfo(
            payment_id=pay_id,
            status="approved",
            external_reference=external_reference,
            transaction_amount=transaction_amount,
        )

    if not settings.mercadopago_access_token:
        raise RuntimeError("mercadopago_access_token requerido cuando mercadopago_mock=False")

    payload: dict[str, Any] = {
        "transaction_amount": float(transaction_amount),
        "token": token,
        "description": description[:256],
        "payment_method_id": payment_method_id,
        "installments": installments,
        "payer": {"email": payer_email},
        "external_reference": external_reference,
    }
    body = json.dumps(payload).encode("utf-8")
    headers = _mp_headers()
    if idempotency_key:
        headers["X-Idempotency-Key"] = idempotency_key
    req = Request(
        "https://api.mercadopago.com/v1/payments",
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Error creando pago con token Mercado Pago: {e}") from e

    raw_amt = data.get("transaction_amount")
    tx_amt: Decimal | None = None
    if raw_amt is not None:
        try:
            tx_amt = Decimal(str(raw_amt))
        except (ValueError, TypeError, ArithmeticError):
            tx_amt = None

    return PagoProveedorInfo(
        payment_id=str(data.get("id", "")),
        status=str(data.get("status", "") or "").lower(),
        external_reference=str(data["external_reference"])
        if data.get("external_reference") is not None
        else None,
        transaction_amount=tx_amt,
    )
