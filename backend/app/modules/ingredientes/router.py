from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.modules.ingredientes.schemas import IngredienteCreate, IngredienteRead, IngredienteUpdate, PaginaIngredientes
from app.modules.ingredientes.exceptions import (
    ErrorIngrediente,
    IngredienteEnUsoError,
    IngredienteNoEncontradoError,
    NombreIngredienteRepetidoError,
)
from app.core.uow.unit_of_work import UnitOfWork
from app.deps.roles import require_stock_o_admin
from app.deps.uow import get_uow
from app.modules.ingredientes.service import _service
from app.modules.usuarios.model import Usuario

router = APIRouter(prefix="/ingredientes", tags=["ingredientes"])


def _map_error(exc: BaseException) -> HTTPException:
    # TODO: agregar logs para debuggear errores en produccion
    if isinstance(exc, IngredienteNoEncontradoError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, NombreIngredienteRepetidoError):
        return HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, IngredienteEnUsoError):
        return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, ErrorIngrediente):
        return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=PaginaIngredientes)
def listar_ingredientes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    es_alergeno: bool | None = Query(None),
    search: str | None = Query(None, max_length=100),
    uow: UnitOfWork = Depends(get_uow),
) -> PaginaIngredientes:
    # traigo todos con paginacion
    try:
        return _service.listar(uow, page, size, es_alergeno, search)
    except ErrorIngrediente as e:
        raise _map_error(e) from e


@router.get("/{ing_id}", response_model=IngredienteRead)
def obtener_ingrediente(
    ing_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> IngredienteRead:
    # si no existe mando 404
    try:
        return _service.obtener(uow, ing_id)
    except ErrorIngrediente as e:
        raise _map_error(e) from e


@router.post("", response_model=IngredienteRead, status_code=status.HTTP_201_CREATED)
def crear_ingrediente(
    body: IngredienteCreate,
    _: Usuario = Depends(require_stock_o_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> IngredienteRead:
    try:
        return _service.crear(uow, body)
    except ErrorIngrediente as e:
        raise _map_error(e) from e


@router.patch("/{ing_id}", response_model=IngredienteRead)
def actualizar_ingrediente(
    ing_id: int,
    body: IngredienteUpdate,
    _: Usuario = Depends(require_stock_o_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> IngredienteRead:
    try:
        return _service.actualizar(uow, ing_id, body)
    except ErrorIngrediente as e:
        raise _map_error(e) from e


@router.delete("/{ing_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_ingrediente(
    ing_id: int,
    _: Usuario = Depends(require_stock_o_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    try:
        _service.eliminar(uow, ing_id)
    except ErrorIngrediente as e:
        raise _map_error(e) from e
