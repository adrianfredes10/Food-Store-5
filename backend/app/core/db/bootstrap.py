"""Arranque de base de datos.

- **SQLite (dev):** crea tablas con `create_all` y aplica semillas.
- **PostgreSQL (entrega):** no ejecuta `create_all`; el esquema debe existir vía Alembic
  (`alembic upgrade head`). Luego se aplican las mismas semillas que en SQLite.
"""

from __future__ import annotations

import logging

from sqlmodel import Session, SQLModel

from app.core.config import settings
from app.core.db import get_engine

logger = logging.getLogger(__name__)


def bootstrap_database() -> None:
    import app.core.db.base  # noqa: F401 — registra todos los modelos en SQLModel.metadata

    url = settings.database_url.strip().lower()
    engine = get_engine()

    if url.startswith("sqlite"):
        SQLModel.metadata.create_all(engine)
        logger.info("SQLite: esquema aplicado con SQLModel.metadata.create_all().")
    else:
        logger.info(
            "Motor no-SQLite: se asume esquema ya creado por Alembic (omitir create_all en bootstrap)."
        )

    from app.db.seed import run_seed, seed_demo_catalog_if_empty

    run_seed()

    with Session(engine) as session:
        seed_demo_catalog_if_empty(session)
        session.commit()

    logger.info("Bootstrap: semillas y catálogo demo verificados.")
