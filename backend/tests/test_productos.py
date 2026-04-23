"""Tests HTTP del catálogo de productos (listado, CRUD admin, stock, soft delete)."""

from __future__ import annotations

class TestListarProductos:
    def test_listar_publico_sin_auth(self, client):
        r = client.get("/api/v1/productos")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body.get("items"), list)

    def test_listar_con_filtro_search(self, client, producto_seed):
        q = producto_seed["nombre"][:6]
        r = client.get("/api/v1/productos", params={"search": q})
        assert r.status_code == 200
        items = r.json()["items"]
        assert any(p["id"] == producto_seed["id"] for p in items)

    def test_listar_con_categoria(self, client, producto_seed):
        cid = producto_seed["categoria_id"]
        r = client.get("/api/v1/productos", params={"categoria_id": cid})
        assert r.status_code == 200
        for p in r.json()["items"]:
            assert p["categoria_id"] == cid

    def test_listar_paginacion(self, client, headers_admin):
        import uuid

        suf = uuid.uuid4().hex[:8]
        rc = client.post(
            "/api/v1/categorias",
            headers=headers_admin,
            json={"nombre": f"PagCat{suf}", "orden": 0, "activo": True},
        )
        assert rc.status_code == 201
        cat_id = rc.json()["id"]
        for i in range(3):
            rp = client.post(
                "/api/v1/productos",
                headers=headers_admin,
                json={
                    "categoria_id": cat_id,
                    "nombre": f"PagProd{suf}_{i}",
                    "precio": "10.00",
                    "stock_cantidad": 1,
                    "disponible": True,
                    "activo": True,
                    "ingredientes": [],
                },
            )
            assert rp.status_code == 201
        r = client.get("/api/v1/productos", params={"page": 1, "size": 2, "search": f"PagProd{suf}"})
        assert r.status_code == 200
        j = r.json()
        assert len(j["items"]) == 2
        assert j["total"] >= 3
        assert j["pages"] >= 2


class TestCrearProducto:
    def test_crear_requiere_admin(self, client, headers_client, producto_seed):
        r = client.post(
            "/api/v1/productos",
            headers=headers_client,
            json={
                "categoria_id": producto_seed["categoria_id"],
                "nombre": "NoAuth",
                "precio": "1.00",
                "stock_cantidad": 1,
                "disponible": True,
                "activo": True,
                "ingredientes": [],
            },
        )
        assert r.status_code == 403

    def test_crear_producto_exitoso(self, client, headers_admin, producto_seed):
        import uuid

        suf = uuid.uuid4().hex[:6]
        r = client.post(
            "/api/v1/productos",
            headers=headers_admin,
            json={
                "categoria_id": producto_seed["categoria_id"],
                "nombre": f"Extra{suf}",
                "descripcion": "x",
                "precio": "15.50",
                "stock_cantidad": 3,
                "disponible": True,
                "activo": True,
                "ingredientes": [],
            },
        )
        assert r.status_code == 201
        j = r.json()
        assert j["id"] is not None
        assert j["nombre"] == f"Extra{suf}"

    def test_crear_precio_negativo_falla(self, client, headers_admin, producto_seed):
        r = client.post(
            "/api/v1/productos",
            headers=headers_admin,
            json={
                "categoria_id": producto_seed["categoria_id"],
                "nombre": "BadPrice",
                "precio": "0",
                "stock_cantidad": 1,
                "disponible": True,
                "activo": True,
                "ingredientes": [],
            },
        )
        assert r.status_code == 422

    def test_crear_stock_negativo_falla(self, client, headers_admin, producto_seed):
        r = client.post(
            "/api/v1/productos",
            headers=headers_admin,
            json={
                "categoria_id": producto_seed["categoria_id"],
                "nombre": "BadStock",
                "precio": "1.00",
                "stock_cantidad": -1,
                "disponible": True,
                "activo": True,
                "ingredientes": [],
            },
        )
        assert r.status_code == 422


class TestStockProducto:
    def test_actualizar_stock_admin(self, client, headers_admin, producto_seed):
        pid = producto_seed["id"]
        r = client.patch(
            f"/api/v1/productos/{pid}/stock",
            headers=headers_admin,
            json={"stock_cantidad": 7},
        )
        assert r.status_code == 200
        assert r.json()["stock_cantidad"] == 7

    def test_actualizar_stock_requiere_auth(self, client, producto_seed):
        r = client.patch(
            f"/api/v1/productos/{producto_seed['id']}/stock",
            json={"stock_cantidad": 1},
        )
        assert r.status_code == 403

    def test_stock_no_puede_ser_negativo(self, client, headers_admin, producto_seed):
        r = client.patch(
            f"/api/v1/productos/{producto_seed['id']}/stock",
            headers=headers_admin,
            json={"stock_cantidad": -1},
        )
        assert r.status_code == 422


class TestSoftDeleteProducto:
    def test_eliminar_producto(self, client, headers_admin, producto_seed):
        pid = producto_seed["id"]
        rd = client.delete(f"/api/v1/productos/{pid}", headers=headers_admin)
        assert rd.status_code == 204
        rg = client.get(f"/api/v1/productos/{pid}")
        assert rg.status_code == 404
