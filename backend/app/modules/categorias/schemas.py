from pydantic import Field, BaseModel


# datos que llegan cuando creamos o editamos una categoria
class CategoriaCreate(BaseModel):
    parent_id: int | None = Field(default=None, ge=1, description="None = categoría raíz")
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str | None = Field(default=None, max_length=10_000)
    orden: int = Field(default=0, ge=0)
    activo: bool = True


class CategoriaUpdate(BaseModel):
    """`parent_id` omitido = sin cambio; `null` = mover a raíz; entero ≥ 1 = nuevo padre."""

    parent_id: int | None = None
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    descripcion: str | None = None
    orden: int | None = Field(default=None, ge=0)
    activo: bool | None = None


# lo que devuelve la api
class CategoriaRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    parent_id: int | None
    nombre: str
    descripcion: str | None
    orden: int
    activo: bool


class PaginaCategorias(BaseModel):
    items: list[CategoriaRead]
    total: int
    page: int
    size: int
    pages: int
