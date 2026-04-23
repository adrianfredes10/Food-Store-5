"""Endpoints /api/v1/pedidos para cliente: listado, detalle, historial, cancelación y búsqueda en catálogo."""

from __future__ import annotations

import json
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.enums import EstadoPedido
from app.core.security.jwt_tokens import create_access_token
from app.core.uow.unit_of_work import UnitOfWork
from app.modules.pagos.model import FormaPago
from app.modules.pedidos.service import PedidoService
from app.modules.productos.model import Categoria, Producto
def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_and_token(client: TestClient, email: str, password: str = "secreto123") -> tuple[str, int]:
    """Registra y emite JWT sin pasar por /login (evita rate limit en tests)."""
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "nombre": "Py", "apellido": "Test"},
    )
    assert r.status_code == 201, r.text
    uid = int(r.json()["id"])
    return create_access_token(subject_user_id=uid), uid


def _seed_forma_pago_producto(engine) -> tuple[int, str]:
    """Devuelve (producto_id, nombre_producto) del ítem de prueba (evita colisión con catálogo demo id=1)."""
    with Session(engine) as session:
        if session.get(FormaPago, "MERCADOPAGO") is None:
            session.add(FormaPago(codigo="MERCADOPAGO", nombre="MP", habilitado=True))
        cat = Categoria(nombre="Cat pytest pedidos", parent_id=None)
        session.add(cat)
        session.flush()
        pizza = Producto(
            categoria_id=cat.id,
            nombre="ZZ pytest pizza napolitana",
            precio=Decimal("100.00"),
            stock_cantidad=50,
            disponible=True,
        )
        session.add(pizza)
        session.add(
            Producto(
                categoria_id=cat.id,
                nombre="Empanada carne",
                precio=Decimal("10.00"),
                stock_cantidad=50,
                disponible=True,
            ),
        )
        session.flush()
        assert pizza.id is not None
        pid = pizza.id
        nombre = pizza.nombre
        session.commit()
        return pid, nombre


def _crear_pedido_api(client: TestClient, token: str, producto_id: int) -> int:
    r = client.post(
        "/api/v1/pedidos",
        json={"items": [{"producto_id": producto_id, "cantidad": 1}], "forma_pago_codigo": "MERCADOPAGO"},
        headers=_auth_headers(token),
    )
    assert r.status_code == 201, r.text
    return int(r.json()["id"])


def test_listar_pedidos_solo_propios(client: TestClient, engine) -> None:
    prod_id, _ = _seed_forma_pago_producto(engine)
    t1, _ = _register_and_token(client, "a1@test.com")
    t2, _ = _register_and_token(client, "a2@test.com")
    _crear_pedido_api(client, t1, prod_id)
    r = client.get("/api/v1/pedidos", headers=_auth_headers(t1))
    assert r.status_code == 200
    assert r.json()["total"] == 1
    r2 = client.get("/api/v1/pedidos", headers=_auth_headers(t2))
    assert r2.status_code == 200
    assert r2.json()["total"] == 0


def test_get_pedido_ajeno_404(client: TestClient, engine) -> None:
    prod_id, _ = _seed_forma_pago_producto(engine)
    t1, _ = _register_and_token(client, "b1@test.com")
    t2, _ = _register_and_token(client, "b2@test.com")
    pid = _crear_pedido_api(client, t1, prod_id)
    r = client.get(f"/api/v1/pedidos/{pid}", headers=_auth_headers(t2))
    assert r.status_code == 404


def test_historial_orden_asc(client: TestClient, engine) -> None:
    prod_id, _ = _seed_forma_pago_producto(engine)
    token, uid = _register_and_token(client, "c1@test.com")
    pid = _crear_pedido_api(client, token, prod_id)
    with Session(engine) as session:
        uow = UnitOfWork(session)
        PedidoService().transicionar_estado(
            uow,
            pid,
            EstadoPedido.CONFIRMADO,
            actor_usuario_id=uid,
        )
        session.commit()
    r = client.get(f"/api/v1/pedidos/{pid}/historial", headers=_auth_headers(token))
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2
    fechas = [row["registrado_en"] for row in data]
    assert fechas == sorted(fechas)


def test_delete_cancela_pendiente(client: TestClient, engine) -> None:
    prod_id, _ = _seed_forma_pago_producto(engine)
    token, _ = _register_and_token(client, "d1@test.com")
    pid = _crear_pedido_api(client, token, prod_id)
    r = client.request(
        "DELETE",
        f"/api/v1/pedidos/{pid}",
        content=json.dumps({"motivo": "Ya no lo quiero"}),
        headers={**_auth_headers(token), "Content-Type": "application/json"},
    )
    assert r.status_code == 200
    assert r.json()["estado"] == "CANCELADO"


def test_delete_confirmado_400(client: TestClient, engine) -> None:
    prod_id, _ = _seed_forma_pago_producto(engine)
    token, uid = _register_and_token(client, "e1@test.com")
    pid = _crear_pedido_api(client, token, prod_id)
    with Session(engine) as session:
        uow = UnitOfWork(session)
        PedidoService().transicionar_estado(
            uow,
            pid,
            EstadoPedido.CONFIRMADO,
            actor_usuario_id=uid,
        )
        session.commit()
    r = client.request(
        "DELETE",
        f"/api/v1/pedidos/{pid}",
        content=json.dumps({"motivo": "Intento tarde"}),
        headers={**_auth_headers(token), "Content-Type": "application/json"},
    )
    assert r.status_code == 400


def test_productos_search_pizza(client: TestClient, engine) -> None:
    _seed_forma_pago_producto(engine)
    r = client.get("/api/v1/productos", params={"search": "ZZ pytest"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert "napolitana" in items[0]["nombre"].lower()


def test_detalle_pedido_incluye_detalles(client: TestClient, engine) -> None:
    prod_id, nombre_esperado = _seed_forma_pago_producto(engine)
    token, _ = _register_and_token(client, "f1@test.com")
    pid = _crear_pedido_api(client, token, prod_id)
    r = client.get(f"/api/v1/pedidos/{pid}", headers=_auth_headers(token))
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == pid
    assert len(body["detalles"]) == 1
    assert body["detalles"][0]["nombre_producto"] == nombre_esperado


def test_usuario_sin_pedidos_lista_vacia(client: TestClient, engine) -> None:
    """GET /pedidos sin compras previas devuelve lista vacía."""
    _seed_forma_pago_producto(engine)
    token, _ = _register_and_token(client, "g1@test.com")
    r = client.get("/api/v1/pedidos", headers=_auth_headers(token))
    assert r.status_code == 200
    assert r.json()["items"] == []
