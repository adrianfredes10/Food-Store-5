"""Alembic: migraciones versionadas (PostgreSQL en entrega; SQLite válido para dev).

`target_metadata` debe ser el metadata global de SQLModel tras registrar todos los modelos.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

from app.core.config import settings

# Registra todas las tablas (orden por FK en models_loader).
import app.core.db.base  # noqa: F401

# Imports explícitos CE-04 — dominios: usuarios/roles, tokens, catálogo, pedidos, pagos, direcciones.
from app.modules.direcciones_entrega.model import DireccionEntrega  # noqa: F401
from app.modules.pagos.model import FormaPago, Pago  # noqa: F401
from app.modules.pedidos.model import DetallePedido, EstadoPedido, HistorialEstadoPedido, Pedido  # noqa: F401
from app.modules.productos.model import Categoria, Ingrediente, Producto, ProductoIngrediente  # noqa: F401
from app.modules.refreshtokens.model import RefreshToken  # noqa: F401
from app.modules.usuarios.model import Rol, Usuario, UsuarioRol  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def _migration_engine():
    url = settings.database_url
    kw: dict = {"poolclass": pool.NullPool}
    if url.strip().lower().startswith("sqlite"):
        kw["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kw)


def run_migrations_offline() -> None:
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = _migration_engine()

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
