"""Carga de modelos SQLModel para registrar tablas en metadata (Alembic / create_all).

Se importan primero los módulos con orden fijo por dependencias FK; luego el resto
de subpaquetes que expongan `model.py`, para no omitir modelos nuevos.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Final

import app.modules as modules_package

# Orden explícito: tablas referenciadas por FK deben existir antes en el registry.
MODEL_LOAD_PRIORITY: Final[tuple[str, ...]] = (
    "app.modules.usuarios.model",
    "app.modules.refreshtokens.model",
    "app.modules.direcciones_entrega.model",
    "app.modules.productos.model",
    "app.modules.pedidos.model",
    "app.modules.pagos.model",
)


def import_all_model_modules() -> None:
    imported: set[str] = set()

    for qualified_name in MODEL_LOAD_PRIORITY:
        importlib.import_module(qualified_name)
        imported.add(qualified_name)

    prefix = f"{modules_package.__name__}."
    for _finder, name, _is_pkg in pkgutil.walk_packages(
        modules_package.__path__,
        prefix,
    ):
        if not name.endswith(".model"):
            continue
        if name in imported:
            continue
        importlib.import_module(name)
        imported.add(name)
