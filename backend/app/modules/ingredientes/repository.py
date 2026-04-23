from __future__ import annotations

from sqlmodel import Session, col, select
from sqlalchemy import and_, func

from app.core.repository.base_repository import BaseRepository
from app.modules.productos.model import Ingrediente, Producto, ProductoIngrediente


class IngredienteRepository(BaseRepository[Ingrediente]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Ingrediente)

    def listar_paginado(
        self,
        page: int = 1,
        size: int = 20,
        es_alergeno: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Ingrediente], int]:
        # traigo todos con paginacion
        page = max(1, page)
        size = max(1, size)
        offset = (page - 1) * size

        cond: list = []
        if es_alergeno is not None:
            cond.append(Ingrediente.es_alergeno == es_alergeno)
        if search is not None and search.strip():
            term = f"%{search.strip()}%"
            cond.append(col(Ingrediente.nombre).ilike(term))

        if cond:
            filt = and_(*cond)
            count_stmt = select(func.count()).select_from(Ingrediente).where(filt)
            list_stmt = (
                select(Ingrediente)
                .where(filt)
                .order_by(col(Ingrediente.nombre).asc())
                .offset(offset)
                .limit(size)
            )
        else:
            count_stmt = select(func.count()).select_from(Ingrediente)
            list_stmt = (
                select(Ingrediente)
                .order_by(col(Ingrediente.nombre).asc())
                .offset(offset)
                .limit(size)
            )

        total = int(self._session.exec(count_stmt).one())
        items = list(self._session.exec(list_stmt).all())
        return items, total

    def get_by_nombre(self, nombre: str) -> Ingrediente | None:
        stmt = select(Ingrediente).where(Ingrediente.nombre == nombre)
        return self._session.exec(stmt).first()

    def count_ids_existentes(self, ids: list[int]) -> int:
        if not ids:
            return 0
        stmt = select(func.count()).select_from(Ingrediente).where(col(Ingrediente.id).in_(ids))
        return int(self._session.exec(stmt).one())

    def tiene_productos_activos(self, ingrediente_id: int) -> bool:
        # si tiene productos activos no lo puedo borrar
        stmt = (
            select(func.count())
            .select_from(ProductoIngrediente)
            .join(Producto, Producto.id == ProductoIngrediente.producto_id)
            .where(
                ProductoIngrediente.ingrediente_id == ingrediente_id,
                col(Producto.deleted_at).is_(None),
                Producto.activo.is_(True),
            )
        )
        return int(self._session.exec(stmt).one()) > 0
