from collections.abc import Generator

from app.core.db.session import new_session
from app.core.uow.unit_of_work import UnitOfWork


def get_uow() -> Generator[UnitOfWork, None, None]:
    """Inyecta UoW por request: commit si el handler termina bien; rollback si falla."""
    with new_session() as session:
        uow = UnitOfWork(session)
        try:
            yield uow
        except Exception:
            uow.rollback()
            raise
        else:
            try:
                uow.commit()
            except Exception:
                uow.rollback()
                raise
