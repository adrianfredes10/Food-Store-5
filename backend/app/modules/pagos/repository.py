from sqlalchemy import func
from sqlmodel import Session, col, select

from app.core.enums import EstadoPago
from app.core.repository.base_repository import BaseRepository
from app.modules.pagos.model import FormaPago, Pago


class PagoRepository(BaseRepository[Pago]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Pago)

    def get_by_idempotency_key(self, idempotency_key: str) -> Pago | None:
        stmt = select(Pago).where(Pago.idempotency_key == idempotency_key)
        return self._session.exec(stmt).first()

    def get_by_id_for_update(self, pago_id: int) -> Pago | None:
        stmt = select(Pago).where(Pago.id == pago_id).with_for_update()
        return self._session.exec(stmt).first()

    def get_by_mp_payment_id(self, mp_payment_id: str) -> Pago | None:
        stmt = select(Pago).where(Pago.mp_payment_id == mp_payment_id)
        return self._session.exec(stmt).first()

    def get_forma_pago_por_codigo(self, codigo: str) -> FormaPago | None:
        stmt = select(FormaPago).where(FormaPago.codigo == codigo, col(FormaPago.habilitado).is_(True))
        return self._session.exec(stmt).first()

    def tiene_pago_aprobado(self, pedido_id: int) -> bool:
        stmt = (
            select(func.count())
            .select_from(Pago)
            .where(Pago.pedido_id == pedido_id, Pago.estado == EstadoPago.APROBADO)
        )
        return int(self._session.exec(stmt).one()) > 0

    def get_pendiente_o_procesando_por_pedido(self, pedido_id: int) -> Pago | None:
        stmt = (
            select(Pago)
            .where(
                Pago.pedido_id == pedido_id,
                col(Pago.estado).in_([EstadoPago.PENDIENTE, EstadoPago.PROCESANDO]),
            )
            .order_by(col(Pago.id).desc())
        )
        return self._session.exec(stmt).first()

    def get_pendiente_o_procesando_por_external_reference(self, external_reference: str) -> Pago | None:
        stmt = (
            select(Pago)
            .where(
                Pago.external_reference == external_reference,
                col(Pago.estado).in_([EstadoPago.PENDIENTE, EstadoPago.PROCESANDO]),
            )
            .order_by(col(Pago.id).desc())
        )
        return self._session.exec(stmt).first()

    def get_mas_reciente_por_pedido(self, pedido_id: int) -> Pago | None:
        stmt = select(Pago).where(Pago.pedido_id == pedido_id).order_by(col(Pago.id).desc())
        return self._session.exec(stmt).first()
