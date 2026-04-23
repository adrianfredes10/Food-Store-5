import app.core.db.base  # noqa: F401 — registra modelos antes de sesión/engine
from app.core.db.base import metadata
from app.core.db.session import get_engine, new_session, session_scope

__all__ = ["get_engine", "metadata", "new_session", "session_scope"]
