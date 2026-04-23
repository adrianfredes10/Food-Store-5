from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


class AccessTokenValidationError(Exception):
    """Token ausente, inválido, expirado o con tipo distinto de access."""


def create_access_token(*, subject_user_id: int, expires_delta: timedelta | None = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject_user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token_payload(token: str) -> dict[str, Any]:
    """Decodifica JWT sin validar el claim `type` (uso interno poco frecuente)."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def decode_and_require_access_token(token: str) -> dict[str, Any]:
    """Valida firma, expiración y que el token sea explícitamente de tipo access."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise AccessTokenValidationError("Token inválido o expirado") from e
    if payload.get("type") != "access":
        raise AccessTokenValidationError("Se requiere un access token")
    return payload


def decode_access_token_payload_safe(token: str) -> dict[str, Any] | None:
    try:
        return decode_access_token_payload(token)
    except JWTError:
        return None
