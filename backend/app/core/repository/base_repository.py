from typing import Any, Generic, TypeVar

from sqlmodel import Session, SQLModel, select

ModelT = TypeVar("ModelT", bound=SQLModel)


class BaseRepository(Generic[ModelT]):
    """Acceso a datos genérico; sin lógica de negocio ni commit."""

    __slots__ = ("_model_cls", "_session")

    def __init__(self, session: Session, model_cls: type[ModelT]) -> None:
        self._session = session
        self._model_cls = model_cls

    def get_by_id(self, entity_id: Any) -> ModelT | None:
        return self._session.get(self._model_cls, entity_id)

    def add(self, entity: ModelT) -> ModelT:
        self._session.add(entity)
        return entity

    def delete(self, entity: ModelT) -> None:
        self._session.delete(entity)

    def list_page(self, *, offset: int = 0, limit: int = 100) -> list[ModelT]:
        stmt = select(self._model_cls).offset(offset).limit(limit)
        return list(self._session.exec(stmt).all())
