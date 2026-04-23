from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks

from app.core.config import settings
from app.core.uow.unit_of_work import UnitOfWork
from app.deps.uow import get_uow
from app.deps.roles import require_admin, require_stock_o_admin
from app.integrations.producto_imagen_groq import aplicar_imagen_groq_post_creacion
from app.modules.categorias.exceptions import CategoriaNoEncontradaError
from app.modules.productos.exceptions import (
    ErrorProducto,
    IngredientesInvalidosError,
    ProductoNoEncontradoError,
    StockNegativoError,
)
from app.modules.productos.service import ProductoCatalogoService
from app.modules.productos.schemas import (
    PaginaProductos,
    ProductoCreate,
    ProductoIngredienteSalida,
    ProductoRead,
    ProductoStockUpdate,
    ProductoUpdate,
)
from app.modules.usuarios.model import Usuario

router = APIRouter(prefix="/productos", tags=["productos"])

_service = ProductoCatalogoService()


def _map_error(exc: BaseException) -> HTTPException:
    # mapeo los errores del dominio a respuestas http
    if isinstance(exc, ProductoNoEncontradoError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, CategoriaNoEncontradaError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, (IngredientesInvalidosError, StockNegativoError)):
        return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, ErrorProducto):
        return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=PaginaProductos)
def listar_productos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    categoria_id: int | None = Query(None, ge=1),
    incluir_subcategorias: bool = Query(
        False,
        description="Si true, incluye productos de subcategorías (CTE recursiva sobre categorías).",
    ),
    disponible: bool | None = Query(None),
    search: str | None = Query(None, max_length=100),
    uow: UnitOfWork = Depends(get_uow),
) -> PaginaProductos:
    # traigo todos con paginacion
    try:
        return _service.listar(
            uow,
            page=page,
            size=size,
            categoria_id=categoria_id,
            incluir_subcategorias=incluir_subcategorias,
            disponible=disponible,
            search=search,
        )
    except (ErrorProducto, CategoriaNoEncontradaError) as e:
        raise _map_error(e) from e


@router.get("/{producto_id}", response_model=ProductoRead)
def obtener_producto(
    producto_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> ProductoRead:
    # si no existe mando 404
    try:
        return _service.obtener(uow, producto_id)
    except (ErrorProducto, CategoriaNoEncontradaError) as e:
        raise _map_error(e) from e


@router.post("", response_model=ProductoRead, status_code=status.HTTP_201_CREATED)
def crear_producto(
    body: ProductoCreate,
    background_tasks: BackgroundTasks,
    _: Usuario = Depends(require_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> ProductoRead:
    try:
        created = _service.crear(uow, body)
    except (ErrorProducto, CategoriaNoEncontradaError) as e:
        raise _map_error(e) from e
    sin_imagen = body.imagen_url is None or (
        isinstance(body.imagen_url, str) and not body.imagen_url.strip()
    )
    if sin_imagen and settings.producto_imagen_auto and settings.groq_api_key.strip():
        assert created.id is not None
        background_tasks.add_task(
            aplicar_imagen_groq_post_creacion,
            created.id,
            body.nombre,
            body.descripcion,
        )
    return created


@router.patch("/{producto_id}", response_model=ProductoRead)
def actualizar_producto(
    producto_id: int,
    body: ProductoUpdate,
    _: Usuario = Depends(require_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> ProductoRead:
    try:
        return _service.actualizar(uow, producto_id, body)
    except (ErrorProducto, CategoriaNoEncontradaError) as e:
        raise _map_error(e) from e


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(
    producto_id: int,
    _: Usuario = Depends(require_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    try:
        _service.eliminar_soft(uow, producto_id)
    except (ErrorProducto, CategoriaNoEncontradaError) as e:
        raise _map_error(e) from e


@router.get("/{producto_id}/ingredientes", response_model=list[ProductoIngredienteSalida])
def listar_ingredientes_producto(
    producto_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> list[ProductoIngredienteSalida]:
    # devuelvo los ingredientes asociados al producto
    try:
        return _service.listar_ingredientes_de_producto(uow, producto_id)
    except (ErrorProducto, CategoriaNoEncontradaError) as e:
        raise _map_error(e) from e


@router.patch("/{producto_id}/stock", response_model=ProductoRead)
def actualizar_stock(
    producto_id: int,
    body: ProductoStockUpdate,
    _: Usuario = Depends(require_stock_o_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> ProductoRead:
    # aca actualizo el stock nada mas
    try:
        return _service.actualizar_stock(uow, producto_id, body)
    except (ErrorProducto, CategoriaNoEncontradaError) as e:
        raise _map_error(e) from e
