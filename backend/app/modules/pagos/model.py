from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlmodel import Field, Relationship, SQLModel

from app.core.enums import EstadoPago
from app.modules.pedidos.model import Pedido


def default_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FormaPago(SQLModel, table=True):
    __tablename__ = "forma_pago"

    codigo: str = Field(sa_column=Column(String(20), primary_key=True, nullable=False))
    nombre: str = Field(sa_column=Column(String(120), nullable=False))
    habilitado: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, server_default="true"))

    pagos: list["Pago"] = Relationship(back_populates="forma_pago")


class Pago(SQLModel, table=True):
    __tablename__ = "pagos"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_pagos_idempotency_key"),)

    id: int | None = Field(default=None, primary_key=True)
    pedido_id: int = Field(sa_column=Column(Integer, ForeignKey("pedidos.id", ondelete="RESTRICT"), nullable=False, index=True))
    forma_pago_codigo: str = Field(
        sa_column=Column(String(20), ForeignKey("forma_pago.codigo", ondelete="RESTRICT"), nullable=False, index=True),
    )
    monto: Decimal = Field(sa_column=Column(Numeric(14, 2), nullable=False))
    estado: EstadoPago = Field(
        default=EstadoPago.PENDIENTE,
        sa_column=Column(
            SAEnum(
                EstadoPago,
                name="estado_pago",
                native_enum=False,
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
            ),
            nullable=False,
            server_default=text(f"'{EstadoPago.PENDIENTE.value}'"),
        ),
    )
    idempotency_key: str = Field(sa_column=Column(String(128), nullable=False))
    external_reference: str = Field(sa_column=Column(String(64), nullable=False, index=True))
    mp_payment_id: str | None = Field(default=None, sa_column=Column(String(64), nullable=True, index=True))
    mp_status: str | None = Field(default=None, sa_column=Column(String(32), nullable=True))
    proveedor_referencia_id: str | None = Field(default=None, sa_column=Column(String(128), nullable=True, index=True))
    notas: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=default_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now(), nullable=True),
    )

    pedido: Pedido = Relationship(back_populates="pagos")
    forma_pago: FormaPago = Relationship(back_populates="pagos")
