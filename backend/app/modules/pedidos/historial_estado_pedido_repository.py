"""Repositorio append-only: solo lectura e inserción (sin update/delete expuestos)."""

from sqlmodel import Session, select

from app.modules.pedidos.model import HistorialEstadoPedido


class HistorialEstadoPedidoRepository:
    __slots__ = ("_session",)

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, historial_id: int) -> HistorialEstadoPedido | None:
        return self._session.get(HistorialEstadoPedido, historial_id)

    def listar_por_pedido(self, pedido_id: int, *, limit: int = 500) -> list[HistorialEstadoPedido]:
        stmt = (
            select(HistorialEstadoPedido)
            .where(HistorialEstadoPedido.pedido_id == pedido_id)
            .order_by(HistorialEstadoPedido.registrado_en.asc())
            .limit(limit)
        )
        return list(self._session.exec(stmt).all())

    def get_ultimo_por_pedido_id(self, pedido_id: int) -> HistorialEstadoPedido | None:
        """Último evento por tiempo de registro (y desempate por id)."""
        stmt = (
            select(HistorialEstadoPedido)
            .where(HistorialEstadoPedido.pedido_id == pedido_id)
            .order_by(HistorialEstadoPedido.registrado_en.desc(), HistorialEstadoPedido.id.desc())
            .limit(1)
        )
        return self._session.exec(stmt).first()

    def add(self, registro: HistorialEstadoPedido) -> HistorialEstadoPedido:
        self._session.add(registro)
        return registro
