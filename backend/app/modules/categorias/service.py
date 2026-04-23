from __future__ import annotations

import math
from datetime import datetime, timezone

from app.modules.categorias.schemas import CategoriaCreate, CategoriaRead, CategoriaUpdate, PaginaCategorias
from app.modules.productos.model import Categoria
from app.core.uow.unit_of_work import UnitOfWork
from app.modules.categorias.exceptions import (
    CicloJerarquicoError,
    CategoriaConHijosActivosError,
    CategoriaConProductosActivosError,
    CategoriaNoEncontradaError,
    ErrorCategoria,
    NombreCategoriaRepetidoError,
)


class CategoriaService:
    def listar(
        self,
        uow: UnitOfWork,
        *,
        page: int,
        size: int,
        parent_id: int | None,
        solo_raices: bool,
        activo: bool | None,
    ) -> PaginaCategorias:
        # TODO: mejorar la paginacion cuando haya muchos registros
        page = max(1, page)
        size = min(100, max(1, size))
        offset = (page - 1) * size

        if parent_id is not None and uow.categorias.get_by_id(parent_id) is None:
            raise CategoriaNoEncontradaError(parent_id)

        total = uow.categorias.count_filtrado(
            parent_id=parent_id,
            solo_raices=solo_raices,
            activo=activo,
        )
        rows = uow.categorias.list_paginado(
            parent_id=parent_id,
            solo_raices=solo_raices,
            activo=activo,
            offset=offset,
            limit=size,
        )
        pages = math.ceil(total / size) if total else 0
        items = [CategoriaRead.model_validate(r) for r in rows]
        return PaginaCategorias(items=items, total=total, page=page, size=size, pages=pages)

    def obtener(self, uow: UnitOfWork, categoria_id: int) -> CategoriaRead:
        c = uow.categorias.get_by_id(categoria_id)
        # si no existe mando 404
        if c is None:
            raise CategoriaNoEncontradaError(categoria_id)
        return CategoriaRead.model_validate(c)

    def crear(self, uow: UnitOfWork, data: CategoriaCreate) -> CategoriaRead:
        # 1. verifico que el padre exista si mandaron uno
        if data.parent_id is not None and uow.categorias.get_by_id(data.parent_id) is None:
            raise CategoriaNoEncontradaError(data.parent_id)

        # 2. verifico que no haya otro con el mismo nombre
        hay_duplicado = uow.categorias.existe_otra_mismo_nombre_mismo_padre(
            nombre=data.nombre,
            parent_id=data.parent_id,
            exclude_id=None,
        )
        if hay_duplicado:
            raise NombreCategoriaRepetidoError()

        # 3. creo y guardo
        c = Categoria(
            parent_id=data.parent_id,
            nombre=data.nombre,
            descripcion=data.descripcion,
            orden=data.orden,
            activo=data.activo,
            deleted_at=None,
        )
        uow.categorias.add(c)
        uow.flush()
        assert c.id is not None
        return CategoriaRead.model_validate(c)

    def actualizar(self, uow: UnitOfWork, categoria_id: int, data: CategoriaUpdate) -> CategoriaRead:
        # 1. busco la categoria
        c = uow.categorias.get_by_id(categoria_id, incluir_eliminadas=True)
        if c is None or c.deleted_at is not None:
            raise CategoriaNoEncontradaError(categoria_id)

        payload = data.model_dump(exclude_unset=True)

        # 2. valido el nuevo padre si cambia
        if "parent_id" in payload:
            new_parent_id: int | None = payload["parent_id"]
            if new_parent_id is not None:
                padre = uow.categorias.get_by_id(new_parent_id)
                if padre is None:
                    raise CategoriaNoEncontradaError(new_parent_id)
            descendientes = set(uow.categorias.list_ids_categoria_y_descendientes(categoria_id))
            if new_parent_id is not None and new_parent_id in descendientes:
                raise CicloJerarquicoError()

        # 3. verifico que no haya otro con el mismo nombre
        new_nombre = payload.get("nombre", c.nombre)
        new_parent = c.parent_id
        if "parent_id" in payload:
            new_parent = payload["parent_id"]
        if "nombre" in payload or "parent_id" in payload:
            hay_duplicado = uow.categorias.existe_otra_mismo_nombre_mismo_padre(
                nombre=new_nombre,
                parent_id=new_parent,
                exclude_id=c.id,
            )
            if hay_duplicado:
                raise NombreCategoriaRepetidoError()

        # 4. aplico los cambios
        if "parent_id" in payload:
            c.parent_id = payload["parent_id"]
        if "nombre" in payload:
            c.nombre = payload["nombre"]
        if "descripcion" in payload:
            c.descripcion = payload["descripcion"]
        if "orden" in payload:
            c.orden = payload["orden"]
        if "activo" in payload:
            c.activo = payload["activo"]

        uow.flush()
        return CategoriaRead.model_validate(c)

    def eliminar_soft(self, uow: UnitOfWork, categoria_id: int) -> None:
        c = uow.categorias.get_by_id(categoria_id, incluir_eliminadas=True)
        # si no existe mando 404
        if c is None or c.deleted_at is not None:
            raise CategoriaNoEncontradaError(categoria_id)

        # no se puede borrar si tiene hijos o productos activos
        if uow.categorias.count_hijos_activos(categoria_id) > 0:
            raise CategoriaConHijosActivosError(categoria_id)
        if uow.categorias.count_productos_activos_en_categoria(categoria_id) > 0:
            raise CategoriaConProductosActivosError(categoria_id)

        c.deleted_at = datetime.now(timezone.utc)
        uow.flush()


_service = CategoriaService()
