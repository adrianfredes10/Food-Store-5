class ErrorProducto(Exception):
    """Base de errores del catálogo de productos."""


class ProductoNoEncontradoError(ErrorProducto):
    def __init__(self, producto_id: int) -> None:
        super().__init__(f"Producto {producto_id} no encontrado")
        self.producto_id = producto_id


class IngredientesInvalidosError(ErrorProducto):
    def __init__(self) -> None:
        super().__init__("Uno o más ingredientes no existen")


class StockNegativoError(ErrorProducto):
    def __init__(self) -> None:
        super().__init__("La cantidad de stock no puede ser negativa")


# Re-export: dominio categorías (mismo mensaje / tipo para routers que importaban desde aquí).
from app.modules.categorias.exceptions import CategoriaNoEncontradaError  # noqa: E402

__all__ = [
    "CategoriaNoEncontradaError",
    "ErrorProducto",
    "IngredientesInvalidosError",
    "ProductoNoEncontradoError",
    "StockNegativoError",
]
