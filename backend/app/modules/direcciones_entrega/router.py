from fastapi import APIRouter, Depends, status

from app.core.uow.unit_of_work import UnitOfWork
from app.deps.uow import get_uow
from app.deps.auth import get_current_user
from app.modules.direcciones_entrega.schemas import (
    DireccionEntregaCreate,
    DireccionEntregaRead,
    DireccionEntregaUpdate,
)
from app.modules.direcciones_entrega.service import get_direccion_service
from app.modules.usuarios.model import Usuario

router = APIRouter(prefix="/direcciones", tags=["direcciones"])
_svc = get_direccion_service()


@router.get("", response_model=list[DireccionEntregaRead])
def listar_direcciones(
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> list[DireccionEntregaRead]:
    if usuario.id is None:
        raise ValueError
    # traigo todas las direcciones del usuario
    rows = _svc.listar(uow, usuario.id)
    return [DireccionEntregaRead.model_validate(r) for r in rows]


@router.post("", response_model=DireccionEntregaRead, status_code=status.HTTP_201_CREATED)
def crear_direccion(
    body: DireccionEntregaCreate,
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DireccionEntregaRead:
    if usuario.id is None:
        raise ValueError
    row = _svc.crear(uow, usuario.id, body)
    assert row.id is not None
    return DireccionEntregaRead.model_validate(row)


@router.patch("/{direccion_id}/principal", response_model=DireccionEntregaRead)
def marcar_principal(
    direccion_id: int,
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DireccionEntregaRead:
    if usuario.id is None:
        raise ValueError
    # marco esta como principal y desmarco las otras
    row = _svc.marcar_como_principal(uow, direccion_id, usuario.id)
    return DireccionEntregaRead.model_validate(row)


@router.get("/{direccion_id}", response_model=DireccionEntregaRead)
def obtener_direccion(
    direccion_id: int,
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DireccionEntregaRead:
    if usuario.id is None:
        raise ValueError
    row = _svc.obtener(uow, usuario.id, direccion_id)
    return DireccionEntregaRead.model_validate(row)


@router.patch("/{direccion_id}", response_model=DireccionEntregaRead)
def actualizar_direccion(
    direccion_id: int,
    body: DireccionEntregaUpdate,
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DireccionEntregaRead:
    if usuario.id is None:
        raise ValueError
    row = _svc.actualizar(uow, usuario.id, direccion_id, body)
    return DireccionEntregaRead.model_validate(row)


@router.delete("/{direccion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_direccion(
    direccion_id: int,
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    if usuario.id is None:
        raise ValueError
    _svc.eliminar(uow, usuario.id, direccion_id)
