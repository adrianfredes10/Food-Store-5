"""Configuración pytest: variables de entorno y motor SQLite en memoria con tablas."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "pytest-jwt-secret-key-32chars-min!!")
os.environ.setdefault("PYTEST_DISABLE_RATE_LIMIT", "1")
os.environ.setdefault("MERCADOPAGO_MOCK", "true")
os.environ.setdefault("PRODUCTO_IMAGEN_AUTO", "false")


@pytest.fixture(autouse=True)
def _reset_engine_between_tests() -> Generator[None, None, None]:
    from app.core.db import session as session_mod

    session_mod._engine = None
    yield
    session_mod._engine = None


@pytest.fixture
def engine():
    from app.core.config import get_settings
    from app.core.db import session as session_mod

    get_settings.cache_clear()
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.drop_all(eng)
    SQLModel.metadata.create_all(eng)
    session_mod._engine = eng
    return eng


@pytest.fixture
def client(engine) -> Generator[TestClient, None, None]:
    from app.core.uow.unit_of_work import UnitOfWork
    from app.deps.uow import get_uow
    from app.main import app

    def override_uow():
        with Session(engine) as session:
            uow = UnitOfWork(session)
            try:
                yield uow
            except Exception:
                uow.rollback()
                raise
            else:
                uow.commit()

    app.dependency_overrides[get_uow] = override_uow
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db_session(engine):
    from sqlmodel import Session

    with Session(engine) as session:
        yield session


@pytest.fixture
def admin_token(client) -> str:
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@foodstore.com", "password": "Admin1234!"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def headers_admin(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def client_token(client) -> str:
    import uuid

    email = f"client_{uuid.uuid4().hex[:12]}@example.com"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Cliente123!",
            "nombre": "Cli",
            "apellido": "Ente",
        },
    )
    assert reg.status_code == 201, reg.text
    r = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Cliente123!"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def headers_client(client_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {client_token}"}


@pytest.fixture
def producto_seed(client, headers_admin):
    """Categoría + producto con stock=10 (nombre único para búsquedas)."""
    import uuid

    suf = uuid.uuid4().hex[:8]
    rc = client.post(
        "/api/v1/categorias",
        headers=headers_admin,
        json={"nombre": f"CatSeed{suf}", "orden": 0, "activo": True},
    )
    assert rc.status_code == 201, rc.text
    cat_id = rc.json()["id"]
    nombre = f"ProdSeed{suf}"
    rp = client.post(
        "/api/v1/productos",
        headers=headers_admin,
        json={
            "categoria_id": cat_id,
            "nombre": nombre,
            "descripcion": "pytest",
            "precio": "25.00",
            "stock_cantidad": 10,
            "disponible": True,
            "activo": True,
            "ingredientes": [],
        },
    )
    assert rp.status_code == 201, rp.text
    return rp.json()


@pytest.fixture
def direccion_seed(client, headers_client):
    r = client.post(
        "/api/v1/direcciones",
        headers=headers_client,
        json={
            "alias": "Casa pytest",
            "calle": "Corrientes",
            "numero": "1234",
            "ciudad": "CABA",
            "codigo_postal": "1043",
            "es_principal": True,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()
