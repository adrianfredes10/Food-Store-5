from sqlmodel import Session

from app.modules.auth.repository import AuthRepository
from app.modules.direcciones_entrega.repository import DireccionEntregaRepository
from app.modules.pagos.repository import PagoRepository
from app.modules.pedidos.historial_estado_pedido_repository import HistorialEstadoPedidoRepository
from app.modules.pedidos.repository import PedidoRepository
from app.modules.categorias.repository import CategoriaRepository
from app.modules.ingredientes.repository import IngredienteRepository
from app.modules.productos.repository import (
    ProductoIngredienteRepository,
    ProductoRepository,
)
from app.modules.refreshtokens.repository import RefreshTokenRepository
from app.modules.usuarios.repository import UsuarioRepository


class UnitOfWork:
    """Encapsula la sesión ORM, repositorios y operaciones de transacción.

    Los servicios no deben llamar a commit ni rollback; el ciclo de vida
    lo resuelve la dependencia FastAPI (`get_uow`) tras finalizar el request.

    Los repositorios comparten la misma sesión y se obtienen solo vía UoW
    (no instanciarlos en servicios).
    """

    # los repositorios se crean lazy para no instanciar los que no se usan en el request

    __slots__ = (
        "_session",
        "_repo_auth",
        "_repo_usuarios",
        "_repo_productos",
        "_repo_categorias",
        "_repo_ingredientes",
        "_repo_productos_ingredientes",
        "_repo_pedidos",
        "_repo_historial_estado_pedido",
        "_repo_pagos",
        "_repo_direcciones",
        "_repo_refreshtokens",
    )

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo_auth: AuthRepository | None = None
        self._repo_usuarios: UsuarioRepository | None = None
        self._repo_productos: ProductoRepository | None = None
        self._repo_categorias: CategoriaRepository | None = None
        self._repo_ingredientes: IngredienteRepository | None = None
        self._repo_productos_ingredientes: ProductoIngredienteRepository | None = None
        self._repo_pedidos: PedidoRepository | None = None
        self._repo_historial_estado_pedido: HistorialEstadoPedidoRepository | None = None
        self._repo_pagos: PagoRepository | None = None
        self._repo_direcciones: DireccionEntregaRepository | None = None
        self._repo_refreshtokens: RefreshTokenRepository | None = None

    @property
    def session(self) -> Session:
        return self._session

    @property
    def auth(self) -> AuthRepository:
        if self._repo_auth is None:
            self._repo_auth = AuthRepository(self._session)
        return self._repo_auth

    @property
    def usuarios(self) -> UsuarioRepository:
        if self._repo_usuarios is None:
            self._repo_usuarios = UsuarioRepository(self._session)
        return self._repo_usuarios

    @property
    def productos(self) -> ProductoRepository:
        if self._repo_productos is None:
            self._repo_productos = ProductoRepository(self._session)
        return self._repo_productos

    @property
    def categorias(self) -> CategoriaRepository:
        if self._repo_categorias is None:
            self._repo_categorias = CategoriaRepository(self._session)
        return self._repo_categorias

    @property
    def ingredientes(self) -> IngredienteRepository:
        if self._repo_ingredientes is None:
            self._repo_ingredientes = IngredienteRepository(self._session)
        return self._repo_ingredientes

    @property
    def productos_ingredientes(self) -> ProductoIngredienteRepository:
        if self._repo_productos_ingredientes is None:
            self._repo_productos_ingredientes = ProductoIngredienteRepository(self._session)
        return self._repo_productos_ingredientes

    @property
    def pedidos(self) -> PedidoRepository:
        if self._repo_pedidos is None:
            self._repo_pedidos = PedidoRepository(self._session)
        return self._repo_pedidos

    @property
    def historial_estado_pedido(self) -> HistorialEstadoPedidoRepository:
        if self._repo_historial_estado_pedido is None:
            self._repo_historial_estado_pedido = HistorialEstadoPedidoRepository(self._session)
        return self._repo_historial_estado_pedido

    @property
    def pagos(self) -> PagoRepository:
        if self._repo_pagos is None:
            self._repo_pagos = PagoRepository(self._session)
        return self._repo_pagos

    @property
    def direcciones(self) -> DireccionEntregaRepository:
        if self._repo_direcciones is None:
            self._repo_direcciones = DireccionEntregaRepository(self._session)
        return self._repo_direcciones

    @property
    def refreshtokens(self) -> RefreshTokenRepository:
        if self._repo_refreshtokens is None:
            self._repo_refreshtokens = RefreshTokenRepository(self._session)
        return self._repo_refreshtokens

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def flush(self) -> None:
        # útil para obtener el id generado antes de hacer el commit final
        self._session.flush()
