"""Tests HTTP de categorías (público listar, admin CRUD, reglas de jerarquía)."""

from __future__ import annotations

import uuid


class TestCategorias:
    def test_listar_publico(self, client):
        r = client.get("/api/v1/categorias")
        assert r.status_code == 200
        assert "items" in r.json()

    def test_crear_categoria_raiz(self, client, headers_admin):
        suf = uuid.uuid4().hex[:8]
        r = client.post(
            "/api/v1/categorias",
            headers=headers_admin,
            json={"nombre": f"Raiz{suf}", "orden": 1, "activo": True},
        )
        assert r.status_code == 201
        j = r.json()
        assert j["parent_id"] is None
        assert j["nombre"] == f"Raiz{suf}"

    def test_crear_categoria_hijo(self, client, headers_admin):
        suf = uuid.uuid4().hex[:8]
        rp = client.post(
            "/api/v1/categorias",
            headers=headers_admin,
            json={"nombre": f"Padre{suf}", "orden": 0, "activo": True},
        )
        assert rp.status_code == 201
        padre_id = rp.json()["id"]
        rh = client.post(
            "/api/v1/categorias",
            headers=headers_admin,
            json={"nombre": f"Hijo{suf}", "parent_id": padre_id, "orden": 0, "activo": True},
        )
        assert rh.status_code == 201
        assert rh.json()["parent_id"] == padre_id

    def test_nombre_duplicado_mismo_nivel(self, client, headers_admin):
        suf = uuid.uuid4().hex[:8]
        nombre = f"Dup{suf}"
        r1 = client.post(
            "/api/v1/categorias",
            headers=headers_admin,
            json={"nombre": nombre, "orden": 0, "activo": True},
        )
        assert r1.status_code == 201
        r2 = client.post(
            "/api/v1/categorias",
            headers=headers_admin,
            json={"nombre": nombre, "orden": 1, "activo": True},
        )
        assert r2.status_code == 409

    def test_ciclo_jerarquico_rechazado(self, client, headers_admin):
        suf = uuid.uuid4().hex[:8]
        ra = client.post(
            "/api/v1/categorias",
            headers=headers_admin,
            json={"nombre": f"A{suf}", "orden": 0, "activo": True},
        )
        assert ra.status_code == 201
        id_a = ra.json()["id"]
        rb = client.post(
            "/api/v1/categorias",
            headers=headers_admin,
            json={"nombre": f"B{suf}", "parent_id": id_a, "orden": 0, "activo": True},
        )
        assert rb.status_code == 201
        id_b = rb.json()["id"]
        rc = client.patch(
            f"/api/v1/categorias/{id_b}",
            headers=headers_admin,
            json={"parent_id": id_b},
        )
        assert rc.status_code == 400

    def test_eliminar_sin_productos(self, client, headers_admin):
        suf = uuid.uuid4().hex[:8]
        r = client.post(
            "/api/v1/categorias",
            headers=headers_admin,
            json={"nombre": f"Vacia{suf}", "orden": 0, "activo": True},
        )
        assert r.status_code == 201
        cid = r.json()["id"]
        rd = client.delete(f"/api/v1/categorias/{cid}", headers=headers_admin)
        assert rd.status_code == 204

    def test_eliminar_con_productos_falla(self, client, headers_admin, producto_seed):
        cid = producto_seed["categoria_id"]
        r = client.delete(f"/api/v1/categorias/{cid}", headers=headers_admin)
        assert r.status_code == 409

    def test_requiere_rol_admin_o_stock(self, client, headers_client):
        r = client.post(
            "/api/v1/categorias",
            headers=headers_client,
            json={"nombre": "NoPermitido", "orden": 0, "activo": True},
        )
        assert r.status_code == 403
