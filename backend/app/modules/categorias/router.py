from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.modules.categorias.schemas import CategoriaCreate, CategoriaRead, CategoriaUpdate, PaginaCategorias
from app.modules.categorias.exceptions import (
    CicloJerarquicoError,
    CategoriaConHijosActivosError,
    CategoriaConProductosActivosError,
    CategoriaNoEncontradaError,
    ErrorCategoria,
    NombreCategoriaRepetidoError,
)
from app.core.uow.unit_of_work import UnitOfWork
from app.deps.roles import require_admin
from app.deps.uow import get_uow
from app.modules.categorias.service import _service
from app.modules.usuarios.model import Usuario

router = APIRouter(prefix="/categorias", tags=["categorias"])


def _map_error(exc: BaseException) -> HTTPException:
    if isinstance(exc, CategoriaNoEncontradaError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, NombreCategoriaRepetidoError):
        return HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, CicloJerarquicoError):
        return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, (CategoriaConHijosActivosError, CategoriaConProductosActivosError)):
        return HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, ErrorCategoria):
        return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=PaginaCategorias)
def listar_categorias(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    parent_id: int | None = Query(None, ge=1, description="Filtrar hijas de este padre (omitir para todas las no eliminadas)"),
    solo_raices: bool = Query(False, description="Solo categorías sin padre"),
    activo: bool | None = Query(None, description="Filtrar por activo; omitir = todas"),
    uow: UnitOfWork = Depends(get_uow),
) -> PaginaCategorias:
    # traigo todos con paginacion
    try:
        return _service.listar(
            uow,
            page=page,
            size=size,
            parent_id=parent_id,
            solo_raices=solo_raices,
            activo=activo,
        )
    except ErrorCategoria as e:
        raise _map_error(e) from e


@router.get("/{categoria_id}", response_model=CategoriaRead)
def obtener_categoria(
    categoria_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> CategoriaRead:
    # si no existe mando 404
    try:
        return _service.obtener(uow, categoria_id)
    except ErrorCategoria as e:
        raise _map_error(e) from e


@router.post("", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    body: CategoriaCreate,
    _: Usuario = Depends(require_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> CategoriaRead:
    try:
        return _service.crear(uow, body)
    except ErrorCategoria as e:
        raise _map_error(e) from e


@router.patch("/{categoria_id}", response_model=CategoriaRead)
def actualizar_categoria(
    categoria_id: int,
    body: CategoriaUpdate,
    _: Usuario = Depends(require_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> CategoriaRead:
    try:
        return _service.actualizar(uow, categoria_id, body)
    except ErrorCategoria as e:
        raise _map_error(e) from e


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_categoria(
    categoria_id: int,
    _: Usuario = Depends(require_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    try:
        _service.eliminar_soft(uow, categoria_id)
    except ErrorCategoria as e:
        raise _map_error(e) from e
