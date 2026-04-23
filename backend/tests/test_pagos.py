"""Idempotencia en creación de checkout (misma Idempotency-Key → mismo resultado lógico)."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security.password import hash_password
from app.core.uow.unit_of_work import UnitOfWork
from app.modules.pagos.model import FormaPago
from app.modules.pedidos.service import PedidoService
from app.modules.productos.model import Categoria, Producto
from app.modules.usuarios.model import Usuario


def _seed_pedido_pendiente(engine) -> int:
    with Session(engine) as session:
        uow = UnitOfWork(session)
        if session.get(FormaPago, "MERCADOPAGO") is None:
            session.add(FormaPago(codigo="MERCADOPAGO", nombre="MP", habilitado=True))
        cat = Categoria(nombre="Cat", parent_id=None)
        session.add(cat)
        session.flush()
        prod = Producto(
            categoria_id=cat.id,
            nombre="Item",
            precio=Decimal("10.00"),
            stock_cantidad=10,
            disponible=True,
        )
        session.add(prod)
        user = Usuario(
            email="pay@test.com",
            hashed_password=hash_password("secretito123"),
            nombre="Pay",
            activo=True,
        )
        session.add(user)
        session.flush()
        pedido = PedidoService().crear_pedido(uow, usuario_id=user.id, lineas=[(prod.id, 1, None)])
        session.flush()
        pid = pedido.id
        session.commit()
        assert pid is not None
        return pid


def test_checkout_idempotencia_misma_key(client: TestClient, engine) -> None:
    pedido_id = _seed_pedido_pendiente(engine)
    key = "idem-test-123"
    r1 = client.post(f"/api/v1/pagos/checkout/pedidos/{pedido_id}", headers={"Idempotency-Key": key})
    r2 = client.post(f"/api/v1/pagos/checkout/pedidos/{pedido_id}", headers={"Idempotency-Key": key})
    assert r1.status_code == 201
    assert r2.status_code == 201
    j1 = r1.json()
    j2 = r2.json()
    assert j1["pago_id"] == j2["pago_id"]
    assert j1["external_reference"] == j2["external_reference"]


def _crear_pedido_y_checkout(client, headers_client, producto_seed, direccion_seed, *, cantidad: int = 2):
    r = client.post(
        "/api/v1/pedidos",
        headers=headers_client,
        json={
            "items": [{"producto_id": producto_seed["id"], "cantidad": cantidad}],
            "direccion_entrega_id": direccion_seed["id"],
        },
    )
    assert r.status_code == 201
    pedido_id = r.json()["id"]
    ch = client.post(f"/api/v1/pagos/checkout/pedidos/{pedido_id}")
    assert ch.status_code == 201
    return pedido_id


class TestWebhookPago:
    def test_webhook_approved_confirma_pedido(self, client, headers_client, producto_seed, direccion_seed):
        cantidad = 2
        stock_ini = producto_seed["stock_cantidad"]
        pid = producto_seed["id"]
        pedido_id = _crear_pedido_y_checkout(
            client,
            headers_client,
            producto_seed,
            direccion_seed,
            cantidad=cantidad,
        )
        pay_id = "MOCK-PAY-WEBHOOK-APPROVE-1"
        wh = client.post(
            "/api/v1/pagos/webhook",
            json={
                "external_reference": str(pedido_id),
                "payment_id": pay_id,
                "status": "approved",
            },
        )
        assert wh.status_code == 200
        gp = client.get(f"/api/v1/pedidos/{pedido_id}", headers=headers_client)
        assert gp.status_code == 200
        assert gp.json()["estado"] == "CONFIRMADO"
        pr = client.get(f"/api/v1/productos/{pid}")
        assert pr.status_code == 200
        assert pr.json()["stock_cantidad"] == stock_ini - cantidad

    def test_webhook_rejected_pedido_sigue_pendiente(self, client, headers_client, producto_seed, direccion_seed):
        pedido_id = _crear_pedido_y_checkout(client, headers_client, producto_seed, direccion_seed)
        wh = client.post(
            "/api/v1/pagos/webhook",
            json={
                "external_reference": str(pedido_id),
                "payment_id": "MOCK-PAY-WEBHOOK-REJ",
                "status": "rejected",
            },
        )
        assert wh.status_code == 200
        gp = client.get(f"/api/v1/pedidos/{pedido_id}", headers=headers_client)
        assert gp.status_code == 200
        assert gp.json()["estado"] == "PENDIENTE"

    def test_webhook_idempotente(self, client, headers_client, producto_seed, direccion_seed):
        cantidad = 2
        stock_ini = producto_seed["stock_cantidad"]
        pid = producto_seed["id"]
        pedido_id = _crear_pedido_y_checkout(
            client,
            headers_client,
            producto_seed,
            direccion_seed,
            cantidad=cantidad,
        )
        pay_id = "MOCK-PAY-WEBHOOK-IDEM"
        payload = {
            "external_reference": str(pedido_id),
            "payment_id": pay_id,
            "status": "approved",
        }
        w1 = client.post("/api/v1/pagos/webhook", json=payload)
        w2 = client.post("/api/v1/pagos/webhook", json=payload)
        assert w1.status_code == 200
        assert w2.status_code == 200
        pr = client.get(f"/api/v1/productos/{pid}")
        assert pr.status_code == 200
        assert pr.json()["stock_cantidad"] == stock_ini - cantidad
        gp = client.get(f"/api/v1/pedidos/{pedido_id}", headers=headers_client)
        assert gp.json()["estado"] == "CONFIRMADO"
