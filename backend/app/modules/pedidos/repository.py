from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

from app.core.enums import EstadoPedido
from app.core.repository.base_repository import BaseRepository
from app.modules.pedidos.model import DetallePedido, HistorialEstadoPedido, Pedido


class PedidoRepository(BaseRepository[Pedido]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Pedido)

    def get_by_id_for_update(self, pedido_id: int, *, nowait: bool = False) -> Pedido | None:
        """Bloquea la fila (SELECT ... FOR UPDATE) hasta el fin de la transacción.

        Usar solo para transiciones de estado; no usar `get_by_id` en ese flujo.
        """
        if nowait:
            return self._session.get(Pedido, pedido_id, with_for_update={"nowait": True})
        return self._session.get(Pedido, pedido_id, with_for_update=True)

    def list_detalles_por_pedido_id(self, pedido_id: int) -> list[DetallePedido]:
        stmt = select(DetallePedido).where(DetallePedido.pedido_id == pedido_id)
        return list(self._session.exec(stmt).all())

    def add_detalle(self, detalle: DetallePedido) -> DetallePedido:
        self._session.add(detalle)
        return detalle

    def count_all(self) -> int:
        stmt = select(func.count()).select_from(Pedido)
        return int(self._session.exec(stmt).one())

    def count_group_by_estado(self) -> dict[str, int]:
        stmt = select(Pedido.estado, func.count()).group_by(Pedido.estado)
        rows = self._session.exec(stmt).all()
        return {row[0].value: int(row[1]) for row in rows}

    def sum_total_entregados(self) -> Decimal:
        stmt = select(func.coalesce(func.sum(Pedido.total), 0)).where(Pedido.estado == EstadoPedido.ENTREGADO)
        raw = self._session.exec(stmt).one()
        return Decimal(str(raw))

    def list_all_ordered_desc(self, offset: int, limit: int) -> list[Pedido]:
        stmt = select(Pedido).order_by(col(Pedido.id).desc()).offset(offset).limit(limit)
        return list(self._session.exec(stmt).all())

    def ventas_diarias_entregados(self, dias: int = 30) -> list[tuple[str, Decimal]]:
        since = datetime.now(timezone.utc) - timedelta(days=dias)
        day_expr = func.date(Pedido.created_at)
        stmt = (
            select(day_expr, func.coalesce(func.sum(Pedido.total), 0))
            .where(Pedido.estado == EstadoPedido.ENTREGADO)
            .where(col(Pedido.created_at) >= since)
            .group_by(day_expr)
            .order_by(day_expr)
        )
        rows = self._session.exec(stmt).all()
        out: list[tuple[str, Decimal]] = []
        for fecha, total in rows:
            fstr = str(fecha) if fecha is not None else ""
            out.append((fstr, Decimal(str(total))))
        return out

    def listar_por_usuario(
        self,
        usuario_id: int,
        page: int = 1,
        size: int = 20,
        estado: EstadoPedido | None = None,
    ) -> tuple[list[Pedido], int]:
        page = max(1, page)
        size = max(1, size)
        offset = (page - 1) * size

        cond = [Pedido.usuario_id == usuario_id]
        if estado is not None:
            cond.append(Pedido.estado == estado)

        count_stmt = select(func.count()).select_from(Pedido).where(*cond)
        total = int(self._session.exec(count_stmt).one())

        stmt = (
            select(Pedido)
            .where(*cond)
            .options(selectinload(Pedido.detalles))
            .order_by(col(Pedido.created_at).desc())
            .offset(offset)
            .limit(size)
        )
        items = list(self._session.exec(stmt).all())
        return items, total

    def get_by_id_y_usuario(self, pedido_id: int, usuario_id: int) -> Pedido | None:
        stmt = select(Pedido).where(Pedido.id == pedido_id, Pedido.usuario_id == usuario_id)
        return self._session.exec(stmt).first()

    def listar_historial(self, pedido_id: int) -> list[HistorialEstadoPedido]:
        stmt = (
            select(HistorialEstadoPedido)
            .where(HistorialEstadoPedido.pedido_id == pedido_id)
            .order_by(col(HistorialEstadoPedido.registrado_en).asc(), col(HistorialEstadoPedido.id).asc())
        )
        return list(self._session.exec(stmt).all())
