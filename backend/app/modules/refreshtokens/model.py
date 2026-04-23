from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlmodel import Field, Relationship, SQLModel


def default_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(sa_column=Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True))
    token_hash: str = Field(sa_column=Column(String(128), unique=True, nullable=False))
    jti: str | None = Field(default=None, sa_column=Column(String(64), unique=True, nullable=True))
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    revoked_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    created_at: datetime = Field(
        default_factory=default_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    user_agent: str | None = Field(default=None, sa_column=Column(String(512), nullable=True))
    ip_origen: str | None = Field(default=None, sa_column=Column(String(64), nullable=True))

    usuario: "Usuario" = Relationship(back_populates="refresh_tokens")  # type: ignore[name-defined]
