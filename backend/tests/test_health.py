"""Smoke: app arranca y /health responde (sin tablas reales)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_ok() -> None:
    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.main import app

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "ok"
