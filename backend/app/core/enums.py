from enum import StrEnum


class EstadoPedido(StrEnum):
    """Estados alineados a la FSM de negocio (transiciones en PedidoService)."""

    PENDIENTE = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"
    EN_PREP = "EN_PREP"
    EN_CAMINO = "EN_CAMINO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"


class EstadoPago(StrEnum):
    PENDIENTE = "PENDIENTE"
    PROCESANDO = "PROCESANDO"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    REEMBOLSADO = "REEMBOLSADO"
