from sqlalchemy import and_, false, func
from sqlmodel import Session, col, select
from decimal import Decimal

from app.modules.productos.model import Producto, ProductoIngrediente


class ProductoRepository:
    __slots__ = ("_session",)

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, producto_id: int, *, incluir_eliminados: bool = False) -> Producto | None:
        # si no existe devuelvo None
        if incluir_eliminados:
            stmt = select(Producto).where(Producto.id == producto_id)
        else:
            stmt = select(Producto).where(
                Producto.id == producto_id,
                col(Producto.deleted_at).is_(None),
            )
        return self._session.exec(stmt).first()

    def add(self, producto: Producto) -> Producto:
        self._session.add(producto)
        return producto

    def count_filtrado(
        self,
        *,
        categoria_ids: list[int] | None,
        disponible: bool | None,
        search: str | None = None,
    ) -> int:
        cond = [col(Producto.deleted_at).is_(None)]
        if categoria_ids is not None:
            if len(categoria_ids) == 0:
                cond.append(false())
            else:
                cond.append(col(Producto.categoria_id).in_(categoria_ids))
        if disponible is not None:
            cond.append(Producto.disponible == disponible)
        if search is not None and (term := search.strip()):
            cond.append(col(Producto.nombre).ilike(f"%{term}%"))
        stmt = select(func.count()).select_from(Producto).where(and_(*cond))
        return int(self._session.exec(stmt).one())

    def list_filtrado_paginado(
        self,
        *,
        categoria_ids: list[int] | None,
        disponible: bool | None,
        search: str | None = None,
        offset: int,
        limit: int,
    ) -> list[Producto]:
        # TODO: mejorar la paginacion cuando haya muchos registros
        # traigo todos con paginacion
        cond = [col(Producto.deleted_at).is_(None)]
        if categoria_ids is not None:
            if len(categoria_ids) == 0:
                cond.append(false())
            else:
                cond.append(col(Producto.categoria_id).in_(categoria_ids))
        if disponible is not None:
            cond.append(Producto.disponible == disponible)
        if search is not None and (term := search.strip()):
            cond.append(col(Producto.nombre).ilike(f"%{term}%"))
        stmt = (
            select(Producto)
            .where(and_(*cond))
            .order_by(col(Producto.id).asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.exec(stmt).all())

    def get_by_id_for_update(
        self,
        producto_id: int,
        *,
        incluir_eliminados: bool = False,
    ) -> Producto | None:
        if incluir_eliminados:
            stmt = select(Producto).where(Producto.id == producto_id).with_for_update()
        else:
            stmt = (
                select(Producto)
                .where(
                    Producto.id == producto_id,
                    col(Producto.deleted_at).is_(None),
                )
                .with_for_update()
            )
        return self._session.exec(stmt).first()


class ProductoIngredienteRepository:
    __slots__ = ("_session",)

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_por_producto(self, producto_id: int) -> list[ProductoIngrediente]:
        stmt = (
            select(ProductoIngrediente)
            .join(Producto, Producto.id == ProductoIngrediente.producto_id)
            .where(
                ProductoIngrediente.producto_id == producto_id,
                col(Producto.deleted_at).is_(None),
            )
        )
        return list(self._session.exec(stmt).all())

    def delete_por_producto(self, producto_id: int) -> None:
        for row in self.list_por_producto(producto_id):
            self._session.delete(row)

    def add(self, row: ProductoIngrediente) -> ProductoIngrediente:
        self._session.add(row)
        return row

    def reemplazar_ingredientes(
        self,
        producto_id: int,
        items: list[tuple[int, Decimal, bool]],
    ) -> None:
        self.delete_por_producto(producto_id)
        for ingrediente_id, cantidad, es_removible in items:
            self.add(
                ProductoIngrediente(
                    producto_id=producto_id,
                    ingrediente_id=ingrediente_id,
                    cantidad=cantidad,
                    es_removible=es_removible,
                ),
            )
