"""Cobertura adicional de auth (sin modificar test_auth.py)."""

from __future__ import annotations

import uuid

from jose import jwt


class TestRegistro:
    def test_registro_exitoso(self, client):
        email = f"reg_{uuid.uuid4().hex[:12]}@example.com"
        r = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Cliente123!", "nombre": "Nombre", "apellido": "Apellido"},
        )
        assert r.status_code == 201
        j = r.json()
        assert j["email"] == email
        assert j["id"] is not None

    def test_email_duplicado(self, client):
        email = f"dup_{uuid.uuid4().hex[:12]}@example.com"
        body = {"email": email, "password": "Cliente123!", "nombre": "Ana", "apellido": "B"}
        assert client.post("/api/v1/auth/register", json=body).status_code == 201
        r2 = client.post("/api/v1/auth/register", json=body)
        assert r2.status_code == 409

    def test_password_corta(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"short_{uuid.uuid4().hex[:8]}@example.com",
                "password": "1234567",
                "nombre": "Al",
                "apellido": "Be",
            },
        )
        assert r.status_code == 422

    def test_rol_client_asignado_automaticamente(self, client):
        email = f"cli_{uuid.uuid4().hex[:12]}@example.com"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Cliente123!", "nombre": "Cli", "apellido": "D"},
        )
        assert reg.status_code == 201
        lg = client.post("/api/v1/auth/login", json={"email": email, "password": "Cliente123!"})
        assert lg.status_code == 200
        token = lg.json()["access_token"]
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        roles = me.json()["roles"]
        assert "CLIENT" in roles
        assert "ADMIN" not in roles
        assert "STOCK" not in roles


class TestLogin:
    def test_credenciales_invalidas(self, client, client_token):
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {client_token}"})
        assert me.status_code == 200
        email = me.json()["email"]
        r = client.post("/api/v1/auth/login", json={"email": email, "password": "MalPassword999!"})
        assert r.status_code == 401

    def test_respuesta_no_diferencia_email_vs_password(self, client, client_token):
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {client_token}"})
        email_ok = me.json()["email"]
        bad_pass = client.post(
            "/api/v1/auth/login",
            json={"email": email_ok, "password": "incorrecta"},
        )
        bad_email = client.post(
            "/api/v1/auth/login",
            json={"email": "noexiste99999@example.com", "password": "Cliente123!"},
        )
        assert bad_pass.status_code == 401
        assert bad_email.status_code == 401
        assert bad_pass.json()["detail"] == bad_email.json()["detail"]

    def test_token_contiene_roles(self, client, client_token):
        claims = jwt.get_unverified_claims(client_token)
        assert claims.get("sub") is not None
        assert claims.get("type") == "access"
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {client_token}"})
        assert me.status_code == 200
        assert "CLIENT" in me.json()["roles"]


class TestRefresh:
    def test_refresh_rota_el_token(self, client, client_token):
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {client_token}"})
        assert me.status_code == 200
        email = me.json()["email"]
        lg = client.post("/api/v1/auth/login", json={"email": email, "password": "Cliente123!"})
        old_refresh = lg.json()["refresh_token"]
        rf = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert rf.status_code == 200
        new_refresh = rf.json()["refresh_token"]
        assert new_refresh != old_refresh

    def test_refresh_token_expirado(self, client):
        r = client.post("/api/v1/auth/refresh", json={"refresh_token": "token-invalido-xyz"})
        assert r.status_code == 401


class TestLogout:
    def test_logout_revoca_refresh_token(self, client):
        email = f"out_{uuid.uuid4().hex[:12]}@example.com"
        assert (
            client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": "Cliente123!", "nombre": "Lu", "apellido": "G"},
            ).status_code
            == 201
        )
        lg = client.post("/api/v1/auth/login", json={"email": email, "password": "Cliente123!"})
        refresh = lg.json()["refresh_token"]
        lo = client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
        assert lo.status_code == 204
        r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert r2.status_code == 401
