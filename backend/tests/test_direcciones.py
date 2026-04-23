"""Tests HTTP de direcciones de entrega (propias, principal, aislamiento entre usuarios)."""

from __future__ import annotations

import uuid


class TestDirecciones:
    def test_listar_direcciones_propias(self, client, headers_client, direccion_seed):
        r = client.get("/api/v1/direcciones", headers=headers_client)
        assert r.status_code == 200
        ids = {d["id"] for d in r.json()}
        assert direccion_seed["id"] in ids

    def test_crear_primera_direccion_es_principal(self, client, headers_client):
        r = client.post(
            "/api/v1/direcciones",
            headers=headers_client,
            json={
                "alias": "primera",
                "calle": "San Martín",
                "numero": "100",
                "ciudad": "Rosario",
                "codigo_postal": "2000",
                "es_principal": False,
            },
        )
        assert r.status_code == 201
        assert r.json()["es_principal"] is True

    def test_crear_segunda_direccion_no_principal(self, client, headers_client):
        r1 = client.post(
            "/api/v1/direcciones",
            headers=headers_client,
            json={
                "alias": "uno",
                "calle": "A",
                "numero": "1",
                "ciudad": "X",
                "codigo_postal": "1000",
            },
        )
        assert r1.status_code == 201
        assert r1.json()["es_principal"] is True
        r2 = client.post(
            "/api/v1/direcciones",
            headers=headers_client,
            json={
                "alias": "dos",
                "calle": "B",
                "numero": "2",
                "ciudad": "Y",
                "codigo_postal": "2000",
            },
        )
        assert r2.status_code == 201
        assert r2.json()["es_principal"] is False

    def test_marcar_principal(self, client, headers_client):
        suf = uuid.uuid4().hex[:6]
        r1 = client.post(
            "/api/v1/direcciones",
            headers=headers_client,
            json={
                "alias": f"p1{suf}",
                "calle": "C1",
                "numero": "1",
                "ciudad": "Z",
                "codigo_postal": "3000",
            },
        )
        r2 = client.post(
            "/api/v1/direcciones",
            headers=headers_client,
            json={
                "alias": f"p2{suf}",
                "calle": "C2",
                "numero": "2",
                "ciudad": "Z",
                "codigo_postal": "3001",
            },
        )
        assert r1.status_code == 201 and r2.status_code == 201
        id1, id2 = r1.json()["id"], r2.json()["id"]
        rm = client.patch(f"/api/v1/direcciones/{id2}/principal", headers=headers_client)
        assert rm.status_code == 200
        lst = client.get("/api/v1/direcciones", headers=headers_client).json()
        by_id = {d["id"]: d for d in lst}
        assert by_id[id2]["es_principal"] is True
        assert by_id[id1]["es_principal"] is False
        principales = [d for d in lst if d["es_principal"]]
        assert len(principales) == 1

    def test_no_ver_direcciones_ajenas(self, client, headers_client):
        email2 = f"u2_{uuid.uuid4().hex[:10]}@example.com"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email2, "password": "Cliente123!", "nombre": "Otro", "apellido": "User"},
        )
        assert reg.status_code == 201
        lg = client.post("/api/v1/auth/login", json={"email": email2, "password": "Cliente123!"})
        assert lg.status_code == 200
        tok2 = lg.json()["access_token"]
        h2 = {"Authorization": f"Bearer {tok2}"}
        rd = client.post(
            "/api/v1/direcciones",
            headers=h2,
            json={
                "alias": "ajena",
                "calle": "X",
                "numero": "9",
                "ciudad": "W",
                "codigo_postal": "9999",
            },
        )
        assert rd.status_code == 201
        ajena_id = rd.json()["id"]
        mine = client.get("/api/v1/direcciones", headers=headers_client).json()
        assert ajena_id not in {d["id"] for d in mine}
