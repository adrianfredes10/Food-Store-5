from __future__ import annotations

import math

from app.modules.ingredientes.schemas import IngredienteCreate, IngredienteRead, IngredienteUpdate, PaginaIngredientes
from app.modules.productos.model import Ingrediente
from app.core.uow.unit_of_work import UnitOfWork
from app.modules.ingredientes.exceptions import (
    IngredienteEnUsoError,
    IngredienteNoEncontradoError,
    NombreIngredienteRepetidoError,
)


class IngredienteService:
    def listar(
        self,
        uow: UnitOfWork,
        page: int,
        size: int,
        es_alergeno: bool | None,
        search: str | None,
    ) -> PaginaIngredientes:
        items, total = uow.ingredientes.listar_paginado(page, size, es_alergeno, search)
        pages = max(1, math.ceil(total / size))
        reads = [IngredienteRead.model_validate(x) for x in items]
        return PaginaIngredientes(items=reads, total=total, page=page, size=size, pages=pages)

    def obtener(self, uow: UnitOfWork, ing_id: int) -> IngredienteRead:
        ing = uow.ingredientes.get_by_id(ing_id)
        # si no existe mando 404
        if ing is None:
            raise IngredienteNoEncontradoError(ing_id)
        return IngredienteRead.model_validate(ing)

    def crear(self, uow: UnitOfWork, data: IngredienteCreate) -> IngredienteRead:
        # 1. verifico que no haya otro con el mismo nombre
        hay_duplicado = uow.ingredientes.get_by_nombre(data.nombre)
        if hay_duplicado is not None:
            raise NombreIngredienteRepetidoError(data.nombre)

        # 2. creo y guardo
        ing = Ingrediente(**data.model_dump())
        uow.ingredientes.add(ing)
        uow.flush()
        assert ing.id is not None
        return IngredienteRead.model_validate(ing)

    def actualizar(self, uow: UnitOfWork, ing_id: int, data: IngredienteUpdate) -> IngredienteRead:
        # 1. busco el ingrediente
        ing = uow.ingredientes.get_by_id(ing_id)
        if ing is None:
            raise IngredienteNoEncontradoError(ing_id)

        payload = data.model_dump(exclude_unset=True)

        # 2. valido nombre si cambia
        if "nombre" in payload and payload["nombre"] is not None and payload["nombre"] != ing.nombre:
            otro = uow.ingredientes.get_by_nombre(payload["nombre"])
            if otro is not None and otro.id != ing.id:
                raise NombreIngredienteRepetidoError(payload["nombre"])
            ing.nombre = payload["nombre"]

        # 3. aplico el resto
        if "unidad" in payload:
            ing.unidad = payload["unidad"]
        if "es_alergeno" in payload:
            ing.es_alergeno = payload["es_alergeno"]

        uow.flush()
        return IngredienteRead.model_validate(ing)

    def eliminar(self, uow: UnitOfWork, ing_id: int) -> None:
        # 1. busco
        ing = uow.ingredientes.get_by_id(ing_id)
        if ing is None:
            raise IngredienteNoEncontradoError(ing_id)

        # 2. verifico que no este en uso en productos activos
        if uow.ingredientes.tiene_productos_activos(ing_id):
            raise IngredienteEnUsoError(ing_id)

        # 3. borro
        uow.ingredientes.delete(ing)
        uow.flush()


_service = IngredienteService()
