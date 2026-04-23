"""Pedido: costo_envio, forma_pago_codigo, snapshot de dirección (spec v5).

Revision ID: 0002_pedido_snapshot
Revises: 0c653a5230b5
Create Date: 2026-04-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_pedido_snapshot"
down_revision: Union[str, Sequence[str], None] = "0c653a5230b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_sqlite() -> bool:
    return op.get_bind().dialect.name == "sqlite"


def upgrade() -> None:
    if _is_sqlite():
        with op.batch_alter_table("pedidos") as batch:
            batch.add_column(
                sa.Column("costo_envio", sa.Numeric(10, 2), nullable=False, server_default="50.00"),
            )
            batch.add_column(sa.Column("forma_pago_codigo", sa.String(20), nullable=True))
            batch.add_column(sa.Column("dir_linea1", sa.Text(), nullable=True))
            batch.add_column(sa.Column("dir_linea2", sa.String(200), nullable=True))
            batch.add_column(sa.Column("dir_ciudad", sa.String(120), nullable=True))
            batch.add_column(sa.Column("dir_provincia", sa.String(80), nullable=True))
            batch.add_column(sa.Column("dir_cp", sa.String(20), nullable=True))
            batch.add_column(sa.Column("dir_alias", sa.String(50), nullable=True))
            batch.create_foreign_key(
                "fk_pedidos_forma_pago_codigo",
                "forma_pago",
                ["forma_pago_codigo"],
                ["codigo"],
                ondelete="SET NULL",
            )
            batch.create_index("ix_pedidos_forma_pago_codigo", ["forma_pago_codigo"])
        return

    op.add_column(
        "pedidos",
        sa.Column("costo_envio", sa.Numeric(10, 2), nullable=False, server_default="50.00"),
    )
    op.add_column("pedidos", sa.Column("forma_pago_codigo", sa.String(20), nullable=True))
    op.add_column("pedidos", sa.Column("dir_linea1", sa.Text(), nullable=True))
    op.add_column("pedidos", sa.Column("dir_linea2", sa.String(200), nullable=True))
    op.add_column("pedidos", sa.Column("dir_ciudad", sa.String(120), nullable=True))
    op.add_column("pedidos", sa.Column("dir_provincia", sa.String(80), nullable=True))
    op.add_column("pedidos", sa.Column("dir_cp", sa.String(20), nullable=True))
    op.add_column("pedidos", sa.Column("dir_alias", sa.String(50), nullable=True))
    op.create_foreign_key(
        "fk_pedidos_forma_pago_codigo",
        "pedidos",
        "forma_pago",
        ["forma_pago_codigo"],
        ["codigo"],
        ondelete="SET NULL",
    )
    op.create_index("ix_pedidos_forma_pago_codigo", "pedidos", ["forma_pago_codigo"])


def downgrade() -> None:
    if _is_sqlite():
        with op.batch_alter_table("pedidos") as batch:
            batch.drop_constraint("fk_pedidos_forma_pago_codigo", type_="foreignkey")
            batch.drop_index("ix_pedidos_forma_pago_codigo")
            batch.drop_column("dir_alias")
            batch.drop_column("dir_cp")
            batch.drop_column("dir_provincia")
            batch.drop_column("dir_ciudad")
            batch.drop_column("dir_linea2")
            batch.drop_column("dir_linea1")
            batch.drop_column("forma_pago_codigo")
            batch.drop_column("costo_envio")
        return

    op.drop_index("ix_pedidos_forma_pago_codigo", table_name="pedidos")
    op.drop_constraint("fk_pedidos_forma_pago_codigo", "pedidos", type_="foreignkey")
    op.drop_column("pedidos", "dir_alias")
    op.drop_column("pedidos", "dir_cp")
    op.drop_column("pedidos", "dir_provincia")
    op.drop_column("pedidos", "dir_ciudad")
    op.drop_column("pedidos", "dir_linea2")
    op.drop_column("pedidos", "dir_linea1")
    op.drop_column("pedidos", "forma_pago_codigo")
    op.drop_column("pedidos", "costo_envio")
