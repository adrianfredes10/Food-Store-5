"""Transiciones de pedido CONFIRMADO → ENTREGADO (servicio de dominio)."""

from __future__ import annotations

from decimal import Decimal

from sqlmodel import Session

from app.core.enums import EstadoPedido
from app.core.security.password import hash_password
from app.core.uow.unit_of_work import UnitOfWork
from app.modules.pagos.model import FormaPago
from app.modules.pedidos.service import PedidoService
from app.modules.productos.model import Categoria, Producto
from app.modules.usuarios.model import Usuario


def test_fsm_confirmado_hasta_entregado(engine) -> None:
    with Session(engine) as session:
        uow = UnitOfWork(session)
        if session.get(FormaPago, "MERCADOPAGO") is None:
            session.add(FormaPago(codigo="MERCADOPAGO", nombre="MP", habilitado=True))
        cat = Categoria(nombre="Cat", parent_id=None)
        session.add(cat)
        session.flush()
        assert cat.id is not None
        prod = Producto(
            categoria_id=cat.id,
            nombre="Item",
            precio=Decimal("50.00"),
            stock_cantidad=5,
            disponible=True,
        )
        session.add(prod)
        user = Usuario(
            email="u@test.com",
            hashed_password=hash_password("secretito123"),
            nombre="U",
            activo=True,
        )
        session.add(user)
        session.flush()
        assert prod.id is not None and user.id is not None

        svc = PedidoService()
        pedido = svc.crear_pedido(uow, usuario_id=user.id, lineas=[(prod.id, 2, None)])
        session.flush()
        assert pedido.id is not None
        assert pedido.estado == EstadoPedido.PENDIENTE

        svc.transicionar_estado(uow, pedido.id, EstadoPedido.CONFIRMADO)
        session.flush()
        p2 = uow.productos.get_by_id(prod.id)
        assert p2 is not None
        assert p2.stock_cantidad == 3

        svc.transicionar_estado(uow, pedido.id, EstadoPedido.EN_PREP)
        svc.transicionar_estado(uow, pedido.id, EstadoPedido.EN_CAMINO)
        svc.transicionar_estado(uow, pedido.id, EstadoPedido.ENTREGADO)
        final = uow.pedidos.get_by_id(pedido.id)
        assert final is not None
        assert final.estado == EstadoPedido.ENTREGADO
        session.commit()


# --- Integración HTTP (FSM y creación de pedidos) ---


def _post_pedido(client, headers_client, producto_seed, direccion_seed, *, cantidad: int = 2, items=None):
    body = {
        "items": items
        or [{"producto_id": producto_seed["id"], "cantidad": cantidad}],
        "direccion_entrega_id": direccion_seed["id"],
    }
    return client.post("/api/v1/pedidos", headers=headers_client, json=body)


class TestCrearPedido:
    def test_crear_pedido_exitoso(self, client, headers_client, producto_seed, direccion_seed):
        precio = Decimal(str(producto_seed["precio"]))
        cantidad = 2
        r = _post_pedido(client, headers_client, producto_seed, direccion_seed, cantidad=cantidad)
        assert r.status_code == 201
        j = r.json()
        assert j["estado"] == "PENDIENTE"
        assert Decimal(str(j["costo_envio"])) == Decimal("50.00")
        esperado = precio * cantidad + Decimal("50.00")
        assert Decimal(str(j["total"])) == esperado

    def test_pedido_sin_items_falla(self, client, headers_client, direccion_seed):
        r = client.post(
            "/api/v1/pedidos",
            headers=headers_client,
            json={"items": [], "direccion_entrega_id": direccion_seed["id"]},
        )
        assert r.status_code == 422

    def test_stock_insuficiente_falla(self, client, headers_client, producto_seed, direccion_seed):
        r = _post_pedido(
            client,
            headers_client,
            producto_seed,
            direccion_seed,
            cantidad=producto_seed["stock_cantidad"] + 5,
        )
        assert r.status_code == 400

    def test_producto_no_disponible_falla(
        self,
        client,
        headers_admin,
        headers_client,
        producto_seed,
        direccion_seed,
    ):
        pid = producto_seed["id"]
        patch = client.patch(
            f"/api/v1/productos/{pid}",
            headers=headers_admin,
            json={"disponible": False},
        )
        assert patch.status_code == 200
        r = _post_pedido(client, headers_client, producto_seed, direccion_seed, cantidad=1)
        assert r.status_code == 400

    def test_snapshot_precio(self, client, headers_admin, headers_client, producto_seed, direccion_seed):
        r0 = _post_pedido(client, headers_client, producto_seed, direccion_seed, cantidad=1)
        assert r0.status_code == 201
        pedido_id = r0.json()["id"]
        snap_antes = Decimal(str(producto_seed["precio"]))
        ch = client.patch(
            f"/api/v1/productos/{producto_seed['id']}",
            headers=headers_admin,
            json={"precio": "99.99"},
        )
        assert ch.status_code == 200
        det = client.get(f"/api/v1/pedidos/{pedido_id}", headers=headers_client)
        assert det.status_code == 200
        lineas = det.json()["detalles"]
        assert len(lineas) == 1
        assert Decimal(str(lineas[0]["precio_unitario_snapshot"])) == snap_antes


class TestFSMPedido:
    def test_cancelar_pedido_pendiente_client(self, client, headers_client, producto_seed, direccion_seed):
        r = _post_pedido(client, headers_client, producto_seed, direccion_seed)
        assert r.status_code == 201
        pid = r.json()["id"]
        rc = client.request(
            "DELETE",
            f"/api/v1/pedidos/{pid}",
            headers=headers_client,
            json={"motivo": "pytest cancela"},
        )
        assert rc.status_code == 200
        assert rc.json()["estado"] == "CANCELADO"

    def test_cancelar_pedido_confirmado_falla_client(
        self,
        client,
        headers_client,
        headers_admin,
        producto_seed,
        direccion_seed,
    ):
        r = _post_pedido(client, headers_client, producto_seed, direccion_seed)
        assert r.status_code == 201
        pid = r.json()["id"]
        tr = client.post(
            f"/api/v1/admin/pedidos/{pid}/transicion",
            headers=headers_admin,
            json={"estado": "CONFIRMADO"},
        )
        assert tr.status_code == 200
        rc = client.request(
            "DELETE",
            f"/api/v1/pedidos/{pid}",
            headers=headers_client,
            json={"motivo": "no debería"},
        )
        assert rc.status_code == 400

    def test_historial_append_only(self, client, headers_client, producto_seed, direccion_seed):
        r = _post_pedido(client, headers_client, producto_seed, direccion_seed)
        assert r.status_code == 201
        pid = r.json()["id"]
        h = client.get(f"/api/v1/pedidos/{pid}/historial", headers=headers_client)
        assert h.status_code == 200
        rows = h.json()
        assert len(rows) == 1
        assert rows[0].get("estado_anterior") is None
        assert rows[0]["estado_nuevo"] == "PENDIENTE"

    def test_transicion_invalida_rechazada(
        self,
        client,
        headers_admin,
        headers_client,
        producto_seed,
        direccion_seed,
    ):
        r = _post_pedido(client, headers_client, producto_seed, direccion_seed)
        assert r.status_code == 201
        pid = r.json()["id"]
        bad = client.post(
            f"/api/v1/admin/pedidos/{pid}/transicion",
            headers=headers_admin,
            json={"estado": "EN_PREP"},
        )
        assert bad.status_code == 400
