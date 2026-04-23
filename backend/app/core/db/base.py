"""Inicializa metadata: registra todas las tablas definidas en app.modules.*.model."""

from sqlmodel import SQLModel

from app.core.db.models_loader import import_all_model_modules

import_all_model_modules()

metadata = SQLModel.metadata

__all__ = ["SQLModel", "metadata"]
