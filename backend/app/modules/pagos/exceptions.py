class ErrorDominioPago(Exception):
    """Base de errores de dominio del módulo pagos."""


class PedidoInvalidoParaPagoError(ErrorDominioPago):
    def __init__(self, pedido_id: int, razon: str) -> None:
        super().__init__(f"Pedido {pedido_id} no admite iniciar pago: {razon}")
        self.pedido_id = pedido_id
        self.razon = razon


class FormaPagoNoConfiguradaError(ErrorDominioPago):
    def __init__(self, codigo: str) -> None:
        super().__init__(f"No hay forma de pago activa con código {codigo!r}")
        self.codigo = codigo


class PagoNoEncontradoError(ErrorDominioPago):
    def __init__(self, detalle: str) -> None:
        super().__init__(f"Pago no encontrado: {detalle}")
        self.detalle = detalle


class PedidoYaTienePagoAprobadoError(ErrorDominioPago):
    def __init__(self, pedido_id: int) -> None:
        super().__init__(f"El pedido {pedido_id} ya tiene un pago aprobado")
        self.pedido_id = pedido_id


class WebhookPagoInvalidoError(ErrorDominioPago):
    def __init__(self, razon: str) -> None:
        super().__init__(f"Webhook de pago inválido: {razon}")
        self.razon = razon
