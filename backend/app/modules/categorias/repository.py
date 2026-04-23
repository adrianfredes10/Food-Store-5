from __future__ import annotations

from sqlmodel import Session, col, select
from sqlalchemy import and_, func, text

from app.modules.productos.model import Categoria, Producto


class CategoriaRepository:
    __slots__ = ("_session",)

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, categoria_id: int, *, incluir_eliminadas: bool = False) -> Categoria | None:
        if incluir_eliminadas:
            return self._session.get(Categoria, categoria_id)
        stmt = select(Categoria).where(
            Categoria.id == categoria_id,
            col(Categoria.deleted_at).is_(None),
        )
        return self._session.exec(stmt).first()

    def add(self, categoria: Categoria) -> Categoria:
        self._session.add(categoria)
        return categoria

    def list_ids_categoria_y_descendientes(self, categoria_raiz_id: int) -> list[int]:
        """Árbol bajo `categoria_raiz_id` (incluye la raíz). CTE recursiva (PostgreSQL / SQLite 3.8.3+)."""
        stmt = text(
            """
            WITH RECURSIVE arbol AS (
                SELECT id FROM categorias WHERE id = :raiz
                UNION ALL
                SELECT c.id
                FROM categorias c
                INNER JOIN arbol a ON c.parent_id = a.id
            )
            SELECT id FROM arbol
            """,
        )
        res = self._session.execute(stmt, {"raiz": categoria_raiz_id})
        return [int(row[0]) for row in res]

    def existe_otra_mismo_nombre_mismo_padre(
        self,
        *,
        nombre: str,
        parent_id: int | None,
        exclude_id: int | None,
    ) -> bool:
        # verifico que no haya otro con el mismo nombre
        cond = [
            Categoria.nombre == nombre,
            col(Categoria.deleted_at).is_(None),
        ]
        if parent_id is None:
            cond.append(col(Categoria.parent_id).is_(None))
        else:
            cond.append(Categoria.parent_id == parent_id)
        if exclude_id is not None:
            cond.append(Categoria.id != exclude_id)
        stmt = select(func.count()).select_from(Categoria).where(and_(*cond))
        return int(self._session.exec(stmt).one()) > 0

    def count_hijos_activos(self, categoria_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Categoria)
            .where(
                Categoria.parent_id == categoria_id,
                Categoria.activo.is_(True),
                col(Categoria.deleted_at).is_(None),
            )
        )
        return int(self._session.exec(stmt).one())

    def count_productos_activos_en_categoria(self, categoria_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Producto)
            .where(
                Producto.categoria_id == categoria_id,
                Producto.activo.is_(True),
                col(Producto.deleted_at).is_(None),
            )
        )
        return int(self._session.exec(stmt).one())

    def count_filtrado(
        self,
        *,
        parent_id: int | None = None,
        solo_raices: bool = False,
        activo: bool | None = None,
    ) -> int:
        """Si `solo_raices`, solo raíz. Si no, y `parent_id` es int, hijos de ese padre. Si no hay filtro de padre, todas las categorías no eliminadas."""
        cond = [col(Categoria.deleted_at).is_(None)]
        if solo_raices:
            cond.append(col(Categoria.parent_id).is_(None))
        elif parent_id is not None:
            cond.append(Categoria.parent_id == parent_id)
        if activo is not None:
            cond.append(Categoria.activo == activo)
        stmt = select(func.count()).select_from(Categoria).where(and_(*cond))
        return int(self._session.exec(stmt).one())

    def list_paginado(
        self,
        *,
        parent_id: int | None = None,
        solo_raices: bool = False,
        activo: bool | None = None,
        offset: int,
        limit: int,
    ) -> list[Categoria]:
        # traigo todos con paginacion
        cond = [col(Categoria.deleted_at).is_(None)]
        if solo_raices:
            cond.append(col(Categoria.parent_id).is_(None))
        elif parent_id is not None:
            cond.append(Categoria.parent_id == parent_id)
        if activo is not None:
            cond.append(Categoria.activo == activo)
        stmt = (
            select(Categoria)
            .where(and_(*cond))
            .order_by(col(Categoria.orden).asc(), col(Categoria.id).asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.exec(stmt).all())
