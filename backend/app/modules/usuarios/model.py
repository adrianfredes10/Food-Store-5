from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlmodel import Field, Relationship, SQLModel


def default_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Rol(SQLModel, table=True):
    __tablename__ = "roles"

    codigo: str = Field(sa_column=Column(String(20), primary_key=True, nullable=False))
    nombre: str = Field(sa_column=Column(String(120), nullable=False))
    descripcion: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    activo: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, server_default="true"))

    usuarios_vinculos: list["UsuarioRol"] = Relationship(
        back_populates="rol",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(sa_column=Column(String(254), unique=True, nullable=False, index=True))
    hashed_password: str = Field(sa_column=Column(String(60), nullable=False))
    nombre: str = Field(sa_column=Column(String(80), nullable=False))
    apellido: str | None = Field(default=None, sa_column=Column(String(80), nullable=True))
    telefono: str | None = Field(default=None, sa_column=Column(String(40), nullable=True))
    activo: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, server_default="true"))
    created_at: datetime = Field(
        default_factory=default_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now(), nullable=True),
    )

    roles_vinculos: list["UsuarioRol"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    refresh_tokens: list["RefreshToken"] = Relationship(  # type: ignore[name-defined]
        back_populates="usuario",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    direcciones: list["DireccionEntrega"] = Relationship(  # type: ignore[name-defined]
        back_populates="usuario",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    pedidos: list["Pedido"] = Relationship(back_populates="usuario")  # type: ignore[name-defined]
    historial_acciones_pedido: list["HistorialEstadoPedido"] = Relationship(  # type: ignore[name-defined]
        back_populates="actor_usuario",
    )


class UsuarioRol(SQLModel, table=True):
    __tablename__ = "usuario_rol"
    __table_args__ = (UniqueConstraint("usuario_id", "rol_codigo", name="uq_usuario_rol_usuario_rol"),)

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(sa_column=Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True))
    rol_codigo: str = Field(sa_column=Column(String(20), ForeignKey("roles.codigo", ondelete="CASCADE"), nullable=False, index=True))
    asignado_en: datetime = Field(
        default_factory=default_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )

    usuario: Usuario = Relationship(back_populates="roles_vinculos")
    rol: Rol = Relationship(back_populates="usuarios_vinculos")
