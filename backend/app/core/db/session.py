from collections.abc import Generator

from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from app.core.config import settings

_engine: Engine | None = None


def _engine_kwargs() -> dict:
    """SQLite necesita `check_same_thread=False` con FastAPI; PostgreSQL usa pool estándar."""
    url = settings.database_url.strip().lower()
    kwargs: dict = {"echo": settings.debug, "pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return kwargs


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url, **_engine_kwargs())
    return _engine


def new_session() -> Session:
    return Session(get_engine())


def session_scope() -> Generator[Session, None, None]:
    """Uso interno; los routers dependen de UoW."""
    with new_session() as session:
        yield session
