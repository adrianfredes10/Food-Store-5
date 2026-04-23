class ErrorCategoria(Exception):
    """Base de errores del dominio categorías."""


class CategoriaNoEncontradaError(ErrorCategoria):
    def __init__(self, categoria_id: int) -> None:
        super().__init__(f"Categoría {categoria_id} no encontrada")
        self.categoria_id = categoria_id


class CategoriaConProductosActivosError(ErrorCategoria):
    def __init__(self, categoria_id: int) -> None:
        super().__init__(f"La categoría {categoria_id} tiene productos activos asociados")
        self.categoria_id = categoria_id


class CategoriaConHijosActivosError(ErrorCategoria):
    def __init__(self, categoria_id: int) -> None:
        super().__init__(f"La categoría {categoria_id} tiene subcategorías activas")
        self.categoria_id = categoria_id


class NombreCategoriaRepetidoError(ErrorCategoria):
    def __init__(self) -> None:
        super().__init__("Ya existe una categoría con ese nombre en este nivel")


class CicloJerarquicoError(ErrorCategoria):
    def __init__(self) -> None:
        super().__init__("La asignación generaría un ciclo en la jerarquía")
