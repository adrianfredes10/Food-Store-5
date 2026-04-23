"""Reglas de negocio del catálogo de productos. Sin commit."""

from __future__ import annotations

import math
from decimal import Decimal
from datetime import datetime, timezone

from app.core.uow.unit_of_work import UnitOfWork
from app.modules.categorias.exceptions import CategoriaNoEncontradaError
from app.modules.productos.exceptions import (
    IngredientesInvalidosError,
    ProductoNoEncontradoError,
    StockNegativoError,
)
from app.modules.productos.model import Producto
from app.modules.productos.schemas import (
    PaginaProductos,
    ProductoCreate,
    ProductoIngredienteEntrada,
    ProductoIngredienteSalida,
    ProductoListadoItem,
    ProductoRead,
    ProductoStockUpdate,
    ProductoUpdate,
)


class ProductoCatalogoService:
    @staticmethod
    def _sincronizar_disponible_con_stock(p: Producto) -> None:
        """Sin stock no puede ofrecerse a la venta: disponible se fuerza a False."""
        hay_stock = p.stock_cantidad > 0
        if not hay_stock:
            p.disponible = False

    def listar(
        self,
        uow: UnitOfWork,
        *,
        page: int,
        size: int,
        categoria_id: int | None,
        incluir_subcategorias: bool,
        disponible: bool | None,
        search: str | None = None,
    ) -> PaginaProductos:
        # traigo todos con paginacion
        page = max(1, page)
        size = min(100, max(1, size))
        offset = (page - 1) * size

        categoria_ids: list[int] | None = None
        if categoria_id is not None:
            if uow.categorias.get_by_id(categoria_id) is None:
                raise CategoriaNoEncontradaError(categoria_id)
            if incluir_subcategorias:
                categoria_ids = uow.categorias.list_ids_categoria_y_descendientes(categoria_id)
            else:
                categoria_ids = [categoria_id]

        total = uow.productos.count_filtrado(
            categoria_ids=categoria_ids,
            disponible=disponible,
            search=search,
        )
        rows = uow.productos.list_filtrado_paginado(
            categoria_ids=categoria_ids,
            disponible=disponible,
            search=search,
            offset=offset,
            limit=size,
        )
        pages = math.ceil(total / size) if total else 0
        items: list[ProductoListadoItem] = []
        for r in rows:
            assert r.id is not None
            base = ProductoListadoItem.model_validate(r)
            ings = self._ingredientes_salida(uow, r.id)
            items.append(base.model_copy(update={"ingredientes": ings}))
        return PaginaProductos(items=items, total=total, page=page, size=size, pages=pages)

    def obtener(self, uow: UnitOfWork, producto_id: int) -> ProductoRead:
        # si no existe mando 404
        prod = uow.productos.get_by_id(producto_id)
        if prod is None:
            raise ProductoNoEncontradoError(producto_id)
        return self._armar_read(uow, prod)

    def crear(self, uow: UnitOfWork, data: ProductoCreate) -> ProductoRead:
        # TODO: validar que el precio no supere un maximo
        # 1. verifico que la categoria exista
        if uow.categorias.get_by_id(data.categoria_id) is None:
            raise CategoriaNoEncontradaError(data.categoria_id)
        # 2. valido los ingredientes
        self._validar_lista_ingredientes(uow, data.ingredientes)
        if data.stock_cantidad < 0:
            raise StockNegativoError()

        # 3. armo el objeto producto
        p = Producto(
            categoria_id=data.categoria_id,
            nombre=data.nombre,
            descripcion=data.descripcion,
            precio=data.precio,
            sku=data.sku,
            imagen_url=data.imagen_url,
            activo=data.activo,
            disponible=data.disponible,
            stock_cantidad=data.stock_cantidad,
            deleted_at=None,
        )
        self._sincronizar_disponible_con_stock(p)
        # 4. guardo en la base
        uow.productos.add(p)
        uow.flush()
        assert p.id is not None
        self._persistir_ingredientes(uow, p.id, data.ingredientes)
        uow.flush()
        return self._armar_read(uow, p)

    def actualizar(self, uow: UnitOfWork, producto_id: int, data: ProductoUpdate) -> ProductoRead:
        # si no existe mando 404
        p = uow.productos.get_by_id(producto_id, incluir_eliminados=True)
        if p is None or p.deleted_at is not None:
            raise ProductoNoEncontradoError(producto_id)

        payload = data.model_dump(exclude_unset=True)
        if "categoria_id" in payload:
            cid = payload["categoria_id"]
            if uow.categorias.get_by_id(cid) is None:
                raise CategoriaNoEncontradaError(cid)
            p.categoria_id = cid
        if "nombre" in payload:
            p.nombre = payload["nombre"]
        if "descripcion" in payload:
            p.descripcion = payload["descripcion"]
        if "precio" in payload:
            p.precio = payload["precio"]
        if "sku" in payload:
            p.sku = payload["sku"]
        if "imagen_url" in payload:
            p.imagen_url = payload["imagen_url"]
        if "activo" in payload:
            p.activo = payload["activo"]
        if "disponible" in payload:
            p.disponible = payload["disponible"]

        if "ingredientes" in payload and payload["ingredientes"] is not None:
            ings = [ProductoIngredienteEntrada.model_validate(x) for x in payload["ingredientes"]]
            self._validar_lista_ingredientes(uow, ings)
            self._persistir_ingredientes(uow, p.id, ings)

        self._sincronizar_disponible_con_stock(p)
        uow.flush()
        return self._armar_read(uow, p)

    def eliminar_soft(self, uow: UnitOfWork, producto_id: int) -> None:
        # si no existe mando 404
        p = uow.productos.get_by_id(producto_id, incluir_eliminados=True)
        if p is None or p.deleted_at is not None:
            raise ProductoNoEncontradoError(producto_id)
        p.deleted_at = datetime.now(timezone.utc)

    def _ingredientes_salida(self, uow: UnitOfWork, producto_id: int) -> list[ProductoIngredienteSalida]:
        vinculos = uow.productos_ingredientes.list_por_producto(producto_id)
        salida: list[ProductoIngredienteSalida] = []
        for v in vinculos:
            ing = uow.ingredientes.get_by_id(v.ingrediente_id)
            if ing is None:
                continue
            salida.append(
                ProductoIngredienteSalida(
                    ingrediente_id=ing.id,
                    nombre=ing.nombre,
                    es_alergeno=ing.es_alergeno,
                    cantidad=v.cantidad,
                    es_removible=v.es_removible,
                ),
            )
        return salida

    def listar_ingredientes_de_producto(self, uow: UnitOfWork, producto_id: int) -> list[ProductoIngredienteSalida]:
        prod = uow.productos.get_by_id(producto_id)
        if prod is None:
            raise ProductoNoEncontradoError(producto_id)
        return self._ingredientes_salida(uow, producto_id)

    def actualizar_stock(self, uow: UnitOfWork, producto_id: int, data: ProductoStockUpdate) -> ProductoRead:
        # si no existe mando 404
        p = uow.productos.get_by_id_for_update(producto_id)
        if p is None:
            raise ProductoNoEncontradoError(producto_id)
        if data.stock_cantidad < 0:
            raise StockNegativoError()
        # aca actualizo el stock
        p.stock_cantidad = data.stock_cantidad
        self._sincronizar_disponible_con_stock(p)
        uow.flush()
        return self._armar_read(uow, p)

    def _validar_lista_ingredientes(self, uow: UnitOfWork, items: list[ProductoIngredienteEntrada]) -> None:
        if not items:
            return
        ids = [i.ingrediente_id for i in items]
        if len(ids) != len(set(ids)):
            raise IngredientesInvalidosError()
        uniq = list(set(ids))
        if uow.ingredientes.count_ids_existentes(uniq) != len(uniq):
            raise IngredientesInvalidosError()

    def _persistir_ingredientes(
        self,
        uow: UnitOfWork,
        producto_id: int,
        items: list[ProductoIngredienteEntrada],
    ) -> None:
        tuples = [(i.ingrediente_id, i.cantidad, i.es_removible) for i in items]
        uow.productos_ingredientes.reemplazar_ingredientes(producto_id, tuples)

    def _armar_read(self, uow: UnitOfWork, p: Producto) -> ProductoRead:
        vinculos = uow.productos_ingredientes.list_por_producto(p.id)
        salida: list[ProductoIngredienteSalida] = []
        for v in vinculos:
            ing = uow.ingredientes.get_by_id(v.ingrediente_id)
            if ing is None:
                continue
            salida.append(
                ProductoIngredienteSalida(
                    ingrediente_id=ing.id,
                    nombre=ing.nombre,
                    es_alergeno=ing.es_alergeno,
                    cantidad=v.cantidad,
                    es_removible=v.es_removible,
                ),
            )
        return ProductoRead(
            id=p.id,
            categoria_id=p.categoria_id,
            nombre=p.nombre,
            descripcion=p.descripcion,
            precio=p.precio,
            sku=p.sku,
            imagen_url=p.imagen_url,
            activo=p.activo,
            disponible=p.disponible,
            stock_cantidad=p.stock_cantidad,
            ingredientes=salida,
        )
