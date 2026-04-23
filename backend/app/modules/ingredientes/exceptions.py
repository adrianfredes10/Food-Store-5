class ErrorIngrediente(Exception):
    """Base de errores del dominio ingredientes."""


class IngredienteNoEncontradoError(ErrorIngrediente):
    def __init__(self, ingrediente_id: int) -> None:
        super().__init__(f"Ingrediente {ingrediente_id} no encontrado")
        self.ingrediente_id = ingrediente_id


class NombreIngredienteRepetidoError(ErrorIngrediente):
    def __init__(self, nombre: str) -> None:
        super().__init__(f"Ya existe un ingrediente con el nombre '{nombre}'")
        self.nombre = nombre


class IngredienteEnUsoError(ErrorIngrediente):
    def __init__(self, ingrediente_id: int) -> None:
        super().__init__(f"El ingrediente {ingrediente_id} está asociado a productos activos")
        self.ingrediente_id = ingrediente_id
