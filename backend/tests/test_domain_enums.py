"""Comprobaciones sin base de datos."""

from __future__ import annotations

from app.core.enums import EstadoPago, EstadoPedido


def test_estado_pedido_fsm_values() -> None:
    assert EstadoPedido.PENDIENTE.value == "PENDIENTE"
    assert EstadoPedido.CONFIRMADO.value == "CONFIRMADO"


def test_estado_pago_values() -> None:
    assert EstadoPago.PENDIENTE.value == "PENDIENTE"
    assert EstadoPago.APROBADO.value == "APROBADO"
