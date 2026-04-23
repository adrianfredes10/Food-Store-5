from pydantic import Field, BaseModel


# lo que manda el cliente al crear
class IngredienteCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=160)
    unidad: str | None = Field(default=None, max_length=32)
    es_alergeno: bool = False


class IngredienteUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=160)
    unidad: str | None = None
    es_alergeno: bool | None = None


# lo que devuelve la api
class IngredienteRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nombre: str
    unidad: str | None
    es_alergeno: bool


class PaginaIngredientes(BaseModel):
    items: list[IngredienteRead]
    total: int
    page: int
    size: int
    pages: int
