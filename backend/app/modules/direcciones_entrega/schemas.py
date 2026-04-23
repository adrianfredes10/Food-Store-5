from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.direcciones_entrega.model import DireccionEntrega


class DireccionEntregaBase(BaseModel):
    alias: str | None = Field(default=None, max_length=80)
    calle: str = Field(min_length=1, max_length=200)
    numero: str = Field(min_length=1, max_length=20)
    piso_dpto: str | None = Field(default=None, max_length=40)
    ciudad: str = Field(min_length=1, max_length=120)
    codigo_postal: str = Field(min_length=1, max_length=20)
    referencias: str | None = Field(default=None, max_length=500)


class DireccionEntregaCreate(DireccionEntregaBase):
    es_principal: bool = False


class DireccionEntregaUpdate(BaseModel):
    alias: str | None = Field(default=None, max_length=80)
    calle: str | None = Field(default=None, min_length=1, max_length=200)
    numero: str | None = Field(default=None, min_length=1, max_length=20)
    piso_dpto: str | None = None
    ciudad: str | None = Field(default=None, min_length=1, max_length=120)
    codigo_postal: str | None = Field(default=None, min_length=1, max_length=20)
    referencias: str | None = None
    es_principal: bool | None = None
    activo: bool | None = None


class DireccionEntregaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    alias: str | None
    calle: str
    numero: str
    piso_dpto: str | None
    ciudad: str
    codigo_postal: str
    referencias: str | None
    es_principal: bool
    activo: bool

    @model_validator(mode="before")
    @classmethod
    def _desde_orm_linea1(cls, data: Any) -> Any:
        if not isinstance(data, DireccionEntrega):
            return data
        raw = (data.linea1 or "").strip()
        calle, numero, ciudad, cp, piso = "", "", "", "", None
        if raw:
            if " (CP " in raw and raw.endswith(")"):
                main, tail = raw.rsplit(" (CP ", 1)
                cp = tail.rstrip(")")
                if ", " in main:
                    addr, ciudad = main.rsplit(", ", 1)
                    ciudad = ciudad.strip()
                else:
                    addr = main.strip()
                if ", " in addr:
                    left, piso = addr.rsplit(", ", 1)
                    addr = left
                else:
                    piso = None
                parts = addr.split(maxsplit=1)
                calle = parts[0]
                numero = parts[1] if len(parts) > 1 else ""
            else:
                parts = raw.split(maxsplit=1)
                calle = parts[0]
                numero = parts[1] if len(parts) > 1 else ""
        return {
            "id": data.id,
            "usuario_id": data.usuario_id,
            "alias": data.alias,
            "calle": calle,
            "numero": numero,
            "piso_dpto": piso,
            "ciudad": ciudad,
            "codigo_postal": cp,
            "referencias": None,
            "es_principal": data.es_principal,
            "activo": data.activo,
        }
