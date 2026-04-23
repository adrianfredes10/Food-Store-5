"""Tests HTTP de ingredientes."""

from __future__ import annotations

import uuid


class TestIngredientes:
    def test_listar_publico(self, client):
        r = client.get("/api/v1/ingredientes")
        assert r.status_code == 200
        assert "items" in r.json()

    def test_filtro_es_alergeno(self, client, headers_admin):
        suf = uuid.uuid4().hex[:8]
        r_ok = client.post(
            "/api/v1/ingredientes",
            headers=headers_admin,
            json={"nombre": f"Aler{suf}", "es_alergeno": True},
        )
        assert r_ok.status_code == 201
        r_no = client.post(
            "/api/v1/ingredientes",
            headers=headers_admin,
            json={"nombre": f"Normal{suf}", "es_alergeno": False},
        )
        assert r_no.status_code == 201
        r_list = client.get("/api/v1/ingredientes", params={"es_alergeno": "true", "search": suf})
        assert r_list.status_code == 200
        items = r_list.json()["items"]
        assert all(x["es_alergeno"] for x in items)
        nombres = {x["nombre"] for x in items}
        assert f"Aler{suf}" in nombres
        assert f"Normal{suf}" not in nombres

    def test_crear_ingrediente(self, client, headers_admin):
        suf = uuid.uuid4().hex[:8]
        r = client.post(
            "/api/v1/ingredientes",
            headers=headers_admin,
            json={"nombre": f"NuevoIng{suf}", "es_alergeno": False},
        )
        assert r.status_code == 201
        assert r.json()["nombre"] == f"NuevoIng{suf}"

    def test_nombre_duplicado(self, client, headers_admin):
        suf = uuid.uuid4().hex[:8]
        nombre = f"DupIng{suf}"
        r1 = client.post(
            "/api/v1/ingredientes",
            headers=headers_admin,
            json={"nombre": nombre, "es_alergeno": False},
        )
        assert r1.status_code == 201
        r2 = client.post(
            "/api/v1/ingredientes",
            headers=headers_admin,
            json={"nombre": nombre, "es_alergeno": False},
        )
        assert r2.status_code == 409

    def test_eliminar_en_uso_falla(self, client, headers_admin, producto_seed):
        suf = uuid.uuid4().hex[:8]
        ri = client.post(
            "/api/v1/ingredientes",
            headers=headers_admin,
            json={"nombre": f"EnUso{suf}", "es_alergeno": False},
        )
        assert ri.status_code == 201
        ing_id = ri.json()["id"]
        pid = producto_seed["id"]
        rp = client.patch(
            f"/api/v1/productos/{pid}",
            headers=headers_admin,
            json={"ingredientes": [{"ingrediente_id": ing_id, "cantidad": "1.000", "es_removible": True}]},
        )
        assert rp.status_code == 200
        rd = client.delete(f"/api/v1/ingredientes/{ing_id}", headers=headers_admin)
        assert rd.status_code == 400
