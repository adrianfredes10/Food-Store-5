from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Enum as SAEnum, ForeignKey, Integer, JSON, Numeric, String, Text, func, text
from sqlmodel import Field, Relationship, SQLModel

from app.core.enums import EstadoPedido as EstadoPedidoEnum
from app.modules.direcciones_entrega.model import DireccionEntrega
from app.modules.productos.model import Producto
from app.modules.usuarios.model import Usuario


def default_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EstadoPedido(SQLModel, table=True):
    __tablename__ = "estados_pedido"

    codigo: str = Field(sa_column=Column(String(20), primary_key=True, nullable=False))
    nombre: str = Field(sa_column=Column(String(100), nullable=False))
    descripcion: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    es_terminal: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, server_default="false"))
    orden: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default="0"))

    pedidos: list["Pedido"] = Relationship(back_populates="estado_entidad")


class Pedido(SQLModel, table=True):
    __tablename__ = "pedidos"

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(sa_column=Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True))
    direccion_entrega_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("direcciones_entrega.id", ondelete="SET NULL"), nullable=True, index=True),
    )
    estado: EstadoPedidoEnum = Field(
        default=EstadoPedidoEnum.PENDIENTE,
        sa_column=Column(
            SAEnum(
                EstadoPedidoEnum,
                name="estado_pedido",
                native_enum=False,
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
            ),
            nullable=False,
            server_default=text(f"'{EstadoPedidoEnum.PENDIENTE.value}'"),
        ),
    )
    estado_codigo: str = Field(
        sa_column=Column(String(20), ForeignKey("estados_pedido.codigo", ondelete="RESTRICT"), nullable=False, index=True, server_default="PENDIENTE"),
    )
    motivo_cancelacion: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    observaciones_cliente: str | None = Field(default=None, sa_column=Column(String(500), nullable=True))
    total: Decimal = Field(sa_column=Column(Numeric(14, 2), nullable=False))
    moneda: str = Field(default="ARS", sa_column=Column(String(3), nullable=False, server_default="ARS"))
    created_at: datetime = Field(
        default_factory=default_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now(), nullable=True),
    )

    costo_envio: Decimal = Field(
        default=Decimal("50.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="50.00"),
    )
    forma_pago_codigo: str | None = Field(
        default=None,
        sa_column=Column(
            String(20),
            ForeignKey("forma_pago.codigo", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )
    dir_linea1: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    dir_linea2: str | None = Field(default=None, sa_column=Column(String(200), nullable=True))
    dir_ciudad: str | None = Field(default=None, sa_column=Column(String(120), nullable=True))
    dir_provincia: str | None = Field(default=None, sa_column=Column(String(80), nullable=True))
    dir_cp: str | None = Field(default=None, sa_column=Column(String(20), nullable=True))
    dir_alias: str | None = Field(default=None, sa_column=Column(String(50), nullable=True))

    usuario: Usuario = Relationship(back_populates="pedidos")
    direccion_entrega: Optional[DireccionEntrega] = Relationship(back_populates="pedidos")
    detalles: list["DetallePedido"] = Relationship(
        back_populates="pedido",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    historial_estados: list["HistorialEstadoPedido"] = Relationship(
        back_populates="pedido",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    pagos: list["Pago"] = Relationship(back_populates="pedido")  # type: ignore[name-defined]
    estado_entidad: EstadoPedido = Relationship(back_populates="pedidos")
    # "FormaPago" en string: evita import circular (pagos.model importa Pedido).
    forma_pago: Optional["FormaPago"] = Relationship()


class DetallePedido(SQLModel, table=True):
    __tablename__ = "detalle_pedido"
    __table_args__ = (CheckConstraint("cantidad > 0", name="ck_detalle_pedido_cantidad_positiva"),)

    id: int | None = Field(default=None, primary_key=True)
    pedido_id: int = Field(sa_column=Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True))
    producto_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("productos.id", ondelete="SET NULL"), nullable=True, index=True),
    )
    nombre_producto: str = Field(sa_column=Column(String(200), nullable=False))
    precio_unitario_snapshot: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    cantidad: int = Field(sa_column=Column(Integer, nullable=False))
    subtotal: Decimal = Field(sa_column=Column(Numeric(14, 2), nullable=False))
    personalizacion: list[int] | None = Field(default=None, sa_column=Column(JSON, nullable=True))

    pedido: Pedido = Relationship(back_populates="detalles")
    producto: Optional[Producto] = Relationship(back_populates="detalles_pedido")


class HistorialEstadoPedido(SQLModel, table=True):
    __tablename__ = "historial_estado_pedido"

    id: int | None = Field(default=None, primary_key=True)
    pedido_id: int = Field(sa_column=Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True))
    estado_anterior: str | None = Field(default=None, sa_column=Column(String(32), nullable=True))
    estado_nuevo: str = Field(sa_column=Column(String(32), nullable=False))
    motivo: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    registrado_en: datetime = Field(
        default_factory=default_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    usuario_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True),
    )

    pedido: Pedido = Relationship(back_populates="historial_estados")
    actor_usuario: Optional[Usuario] = Relationship(back_populates="historial_acciones_pedido")
