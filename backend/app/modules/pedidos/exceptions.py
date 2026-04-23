from app.core.enums import EstadoPedido


class ErrorDominioPedido(Exception):
    """Base de errores de dominio para el agregado pedido."""


class PedidoNoEncontradoError(ErrorDominioPedido):
    def __init__(self, pedido_id: int) -> None:
        super().__init__(f"Pedido {pedido_id} no encontrado")
        self.pedido_id = pedido_id


class PedidoEnEstadoTerminalError(ErrorDominioPedido):
    def __init__(self, pedido_id: int, estado: EstadoPedido) -> None:
        super().__init__(f"Pedido {pedido_id} está en estado terminal ({estado.value})")
        self.pedido_id = pedido_id
        self.estado = estado


class TransicionPedidoInvalidaError(ErrorDominioPedido):
    def __init__(self, pedido_id: int, actual: EstadoPedido, solicitado: EstadoPedido) -> None:
        super().__init__(
            f"Transición inválida para pedido {pedido_id}: {actual.value} → {solicitado.value}",
        )
        self.pedido_id = pedido_id
        self.actual = actual
        self.solicitado = solicitado


class MotivoCancelacionRequeridoError(ErrorDominioPedido):
    def __init__(self, pedido_id: int) -> None:
        super().__init__(f"Cancelar pedido {pedido_id} requiere motivo")
        self.pedido_id = pedido_id


class PedidoSinItemsError(ErrorDominioPedido):
    """No se permite crear un pedido sin al menos una línea de producto."""

    def __init__(self) -> None:
        super().__init__("El pedido debe incluir al menos un producto")


class ProductoNoComprableEnPedidoError(ErrorDominioPedido):
    """El producto no cumple reglas de pedido (vigencia, disponibilidad o stock). Validación propia del módulo pedidos."""

    def __init__(self, producto_id: int, razon: str) -> None:
        super().__init__(f"Producto {producto_id} no puede incluirse en el pedido: {razon}")
        self.producto_id = producto_id
        self.razon = razon


class DireccionEntregaNoValidaError(ErrorDominioPedido):
    def __init__(self, direccion_id: int) -> None:
        super().__init__(f"Dirección de entrega {direccion_id} no válida o no pertenece al usuario")
        self.direccion_id = direccion_id


class FormaPagoNoValidaError(ErrorDominioPedido):
    def __init__(self, codigo: str) -> None:
        super().__init__(f"Forma de pago '{codigo}' no existe o no está habilitada")
        self.codigo = codigo


class PedidoHistorialDesincronizadoError(ErrorDominioPedido):
    """El último registro de historial no refleja el estado actual del pedido."""

    def __init__(
        self,
        pedido_id: int,
        estado_en_pedido: str,
        ultimo_estado_nuevo_en_historial: str | None,
    ) -> None:
        super().__init__(
            f"Pedido {pedido_id} desincronizado con historial: "
            f"pedido.estado={estado_en_pedido!r}, "
            f"último historial.estado_nuevo={ultimo_estado_nuevo_en_historial!r}",
        )
        self.pedido_id = pedido_id
        self.estado_en_pedido = estado_en_pedido
        self.ultimo_estado_nuevo_en_historial = ultimo_estado_nuevo_en_historial
