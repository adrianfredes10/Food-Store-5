from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlmodel import Field, Relationship, SQLModel


def default_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Categoria(SQLModel, table=True):
    __tablename__ = "categorias"
    __table_args__ = (UniqueConstraint("parent_id", "nombre", name="uq_categorias_parent_nombre"),)

    id: int | None = Field(default=None, primary_key=True)
    parent_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True, index=True),
    )
    nombre: str = Field(sa_column=Column(String(120), nullable=False))
    descripcion: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    orden: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default="0"))
    activo: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, server_default="true"))
    deleted_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    parent: Optional["Categoria"] = Relationship(
        back_populates="hijos",
        sa_relationship_kwargs={"remote_side": "Categoria.id"},
    )
    hijos: list["Categoria"] = Relationship(back_populates="parent")
    productos: list["Producto"] = Relationship(back_populates="categoria")


class Ingrediente(SQLModel, table=True):
    __tablename__ = "ingredientes"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(sa_column=Column(String(160), unique=True, nullable=False))
    unidad: str | None = Field(default=None, sa_column=Column(String(32), nullable=True))
    es_alergeno: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, server_default="false"))

    productos_vinculos: list["ProductoIngrediente"] = Relationship(
        back_populates="ingrediente",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Producto(SQLModel, table=True):
    __tablename__ = "productos"
    __table_args__ = (
        UniqueConstraint("sku", name="uq_productos_sku"),
        CheckConstraint("stock_cantidad >= 0", name="ck_productos_stock_no_negativo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    categoria_id: int = Field(sa_column=Column(Integer, ForeignKey("categorias.id", ondelete="RESTRICT"), nullable=False, index=True))
    nombre: str = Field(sa_column=Column(String(200), nullable=False))
    descripcion: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    precio: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    imagen_url: str | None = Field(default=None, sa_column=Column(String(2048), nullable=True))
    sku: str | None = Field(default=None, sa_column=Column(String(64), nullable=True))
    activo: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, server_default="true"))
    disponible: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, server_default="true"))
    stock_cantidad: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default="0"))
    deleted_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    created_at: datetime = Field(
        default_factory=default_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now(), nullable=True),
    )

    categoria: Categoria = Relationship(back_populates="productos")
    ingredientes_vinculos: list["ProductoIngrediente"] = Relationship(
        back_populates="producto",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    detalles_pedido: list["DetallePedido"] = Relationship(  # type: ignore[name-defined]
        back_populates="producto",
    )


class ProductoIngrediente(SQLModel, table=True):
    __tablename__ = "producto_ingrediente"
    __table_args__ = (
        UniqueConstraint("producto_id", "ingrediente_id", name="uq_producto_ingrediente_producto_ingrediente"),
        CheckConstraint("cantidad > 0", name="ck_producto_ingrediente_cantidad_positiva"),
    )

    id: int | None = Field(default=None, primary_key=True)
    producto_id: int = Field(sa_column=Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False, index=True))
    ingrediente_id: int = Field(
        sa_column=Column(Integer, ForeignKey("ingredientes.id", ondelete="CASCADE"), nullable=False, index=True),
    )
    cantidad: Decimal = Field(sa_column=Column(Numeric(10, 3), nullable=False))
    es_removible: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, server_default="true"))

    producto: Producto = Relationship(back_populates="ingredientes_vinculos")
    ingrediente: Ingrediente = Relationship(back_populates="productos_vinculos")
