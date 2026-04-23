from sqlalchemy import update
from sqlmodel import Session, col, select

from app.modules.direcciones_entrega.model import DireccionEntrega


class DireccionEntregaRepository:
    __slots__ = ("_session",)

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, direccion_id: int) -> DireccionEntrega | None:
        return self._session.get(DireccionEntrega, direccion_id)

    def list_by_usuario(self, usuario_id: int, *, solo_activas: bool = True) -> list[DireccionEntrega]:
        stmt = select(DireccionEntrega).where(DireccionEntrega.usuario_id == usuario_id)
        if solo_activas:
            stmt = stmt.where(col(DireccionEntrega.activo).is_(True))
        stmt = stmt.order_by(col(DireccionEntrega.es_principal).desc(), col(DireccionEntrega.id).asc())
        return list(self._session.exec(stmt).all())

    def add(self, row: DireccionEntrega) -> DireccionEntrega:
        self._session.add(row)
        return row

    def delete(self, row: DireccionEntrega) -> None:
        self._session.delete(row)

    def limpiar_principal(self, usuario_id: int) -> None:
        self._session.execute(
            update(DireccionEntrega)
            .where(
                DireccionEntrega.usuario_id == usuario_id,
                col(DireccionEntrega.es_principal).is_(True),
            )
            .values(es_principal=False),
        )
