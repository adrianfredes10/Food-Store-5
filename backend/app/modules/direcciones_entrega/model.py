from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlmodel import Field, Relationship, SQLModel

from app.modules.usuarios.model import Usuario


def default_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DireccionEntrega(SQLModel, table=True):
    __tablename__ = "direcciones_entrega"

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(sa_column=Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True))
    alias: str | None = Field(default=None, sa_column=Column(String(50), nullable=True))
    linea1: str = Field(sa_column=Column(Text, nullable=False))
    es_principal: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, server_default="false"))
    activo: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, server_default="true"))
    created_at: datetime = Field(
        default_factory=default_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )

    usuario: Usuario = Relationship(back_populates="direcciones")
    pedidos: list["Pedido"] = Relationship(back_populates="direccion_entrega")  # type: ignore[name-defined]
