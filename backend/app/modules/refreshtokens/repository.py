from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import update
from sqlmodel import Session, select

from app.core.repository.base_repository import BaseRepository
from app.modules.refreshtokens.model import RefreshToken


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, RefreshToken)

    def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        return self._session.exec(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).first()

    def get_by_token_hash_for_update(self, token_hash: str) -> RefreshToken | None:
        return self._session.exec(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update(),
        ).first()

    def list_activos_por_usuario(self, usuario_id: int) -> Sequence[RefreshToken]:
        stmt = select(RefreshToken).where(
            RefreshToken.usuario_id == usuario_id,
            RefreshToken.revoked_at == None,  # noqa: E711
        )
        return self._session.exec(stmt).all()

    def revocar_todos_activos_por_usuario(self, usuario_id: int) -> None:
        now = datetime.now(timezone.utc)
        self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.usuario_id == usuario_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now),
        )

    def add(self, row: RefreshToken) -> RefreshToken:
        self._session.add(row)
        return row
