from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_y_login(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "pytest_user@example.com",
            "password": "secreto123",
            "nombre": "Py",
            "apellido": "Test",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "pytest_user@example.com"

    r2 = client.post(
        "/api/v1/auth/login",
        json={"email": "pytest_user@example.com", "password": "secreto123"},
    )
    assert r2.status_code == 200
    tok = r2.json()
    assert "access_token" in tok
    assert tok["token_type"] == "bearer"
