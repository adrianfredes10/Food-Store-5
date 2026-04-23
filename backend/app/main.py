from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.core.config import settings
from app.core.db import get_engine
from app.core.db.bootstrap import bootstrap_database
from app.core.rate_limit import limiter
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.direcciones_entrega.router import router as direcciones_router
from app.modules.pagos.router import router as pagos_router
from app.modules.pedidos.router import router as pedidos_router
from app.modules.categorias.router import router as categorias_router
from app.modules.ingredientes.router import router as ingredientes_router
from app.modules.productos.router import router as productos_router

API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap_database()
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    yield
    engine.dispose()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(auth_router, prefix=API_V1_PREFIX)
    application.include_router(admin_router, prefix=API_V1_PREFIX)
    application.include_router(direcciones_router, prefix=API_V1_PREFIX)
    application.include_router(pagos_router, prefix=API_V1_PREFIX)
    application.include_router(pedidos_router, prefix=API_V1_PREFIX)
    application.include_router(productos_router, prefix=API_V1_PREFIX)
    application.include_router(categorias_router, prefix=API_V1_PREFIX)
    application.include_router(ingredientes_router, prefix=API_V1_PREFIX)

    @application.get("/health", tags=["health"])
    def health() -> dict[str, str | bool]:
        out: dict[str, str | bool] = {"status": "ok"}
        if settings.debug:
            out["producto_imagen_auto"] = settings.producto_imagen_auto
            out["groq_configurado"] = bool(settings.groq_api_key.strip())
        return out

    return application


app = create_app()
