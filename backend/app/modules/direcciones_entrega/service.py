"""Reglas de negocio de direcciones. Sin commit."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.modules.direcciones_entrega.model import DireccionEntrega
from app.modules.direcciones_entrega.schemas import (
    DireccionEntregaCreate,
    DireccionEntregaRead,
    DireccionEntregaUpdate,
)

if TYPE_CHECKING:
    from app.core.uow.unit_of_work import UnitOfWork


def _linea1_desde_create(data: DireccionEntregaCreate) -> str:
    base = f"{data.calle.strip()} {data.numero.strip()}"
    if data.piso_dpto:
        base += f", {data.piso_dpto.strip()}"
    return f"{base}, {data.ciudad.strip()} (CP {data.codigo_postal.strip()})"


class DireccionEntregaService:
    def listar(self, uow: UnitOfWork, usuario_id: int) -> list[DireccionEntrega]:
        return uow.direcciones.list_by_usuario(usuario_id)

    def obtener(self, uow: UnitOfWork, usuario_id: int, direccion_id: int) -> DireccionEntrega:
        d = uow.direcciones.get_by_id(direccion_id)
        if d is None or d.usuario_id != usuario_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Dirección no encontrada")
        return d

    def crear(self, uow: UnitOfWork, usuario_id: int, data: DireccionEntregaCreate) -> DireccionEntrega:
        # 1. si es la primera dirección del usuario, la marco como principal automáticamente
        prev = uow.direcciones.list_by_usuario(usuario_id)
        es_principal = True if not prev else data.es_principal
        if es_principal:
            self._quitar_principal_otras(uow, usuario_id)
        # 2. armo el objeto y lo guardo
        row = DireccionEntrega(
            usuario_id=usuario_id,
            alias=data.alias,
            linea1=_linea1_desde_create(data),
            es_principal=es_principal,
            activo=True,
        )
        uow.direcciones.add(row)
        uow.flush()
        return row

    def actualizar(
        self,
        uow: UnitOfWork,
        usuario_id: int,
        direccion_id: int,
        data: DireccionEntregaUpdate,
    ) -> DireccionEntrega:
        # 1. verifico que la dirección exista y sea del usuario
        d = self.obtener(uow, usuario_id, direccion_id)
        payload = data.model_dump(exclude_unset=True)
        # 2. si me piden que sea principal, limpio las otras primero
        if payload.get("es_principal") is True:
            self._quitar_principal_otras(uow, usuario_id, except_id=direccion_id)
        if "alias" in payload:
            d.alias = payload["alias"]
        addr_keys = {"calle", "numero", "piso_dpto", "ciudad", "codigo_postal"}
        if addr_keys & payload.keys():
            cur = DireccionEntregaRead.model_validate(d)
            calle = payload.get("calle", cur.calle) or "-"
            numero = payload.get("numero", cur.numero) or "-"
            piso = payload.get("piso_dpto", cur.piso_dpto)
            ciudad = payload.get("ciudad", cur.ciudad) or "-"
            cp = payload.get("codigo_postal", cur.codigo_postal) or "-"
            tmp = DireccionEntregaCreate(
                alias=cur.alias,
                calle=calle,
                numero=numero,
                piso_dpto=piso,
                ciudad=ciudad,
                codigo_postal=cp,
                referencias=cur.referencias,
                es_principal=cur.es_principal,
            )
            d.linea1 = _linea1_desde_create(tmp)
        if "es_principal" in payload and payload["es_principal"] is not None:
            d.es_principal = payload["es_principal"]
        if "activo" in payload and payload["activo"] is not None:
            d.activo = payload["activo"]
        uow.flush()
        return d

    def eliminar(self, uow: UnitOfWork, usuario_id: int, direccion_id: int) -> None:
        d = self.obtener(uow, usuario_id, direccion_id)
        uow.direcciones.delete(d)

    def marcar_como_principal(self, uow: UnitOfWork, dir_id: int, usuario_id: int) -> DireccionEntrega:
        d = self.obtener(uow, usuario_id, dir_id)
        uow.direcciones.limpiar_principal(usuario_id)
        uow.session.refresh(d)
        d.es_principal = True
        uow.flush()
        return d

    def _quitar_principal_otras(self, uow: UnitOfWork, usuario_id: int, except_id: int | None = None) -> None:
        for o in uow.direcciones.list_by_usuario(usuario_id, solo_activas=False):
            if except_id is not None and o.id == except_id:
                continue
            if o.es_principal:
                o.es_principal = False


_direccion_svc = DireccionEntregaService()


def get_direccion_service() -> DireccionEntregaService:
    return _direccion_svc
