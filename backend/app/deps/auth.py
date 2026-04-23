from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security.jwt_tokens import AccessTokenValidationError, decode_and_require_access_token
from app.core.uow.unit_of_work import UnitOfWork
from app.deps.uow import get_uow
from app.modules.usuarios.model import Usuario

_bearer_required = HTTPBearer(auto_error=True)
_bearer_optional = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer_required),
    uow: UnitOfWork = Depends(get_uow),
) -> Usuario:
    try:
        payload = decode_and_require_access_token(creds.credentials)
        user_id = int(payload["sub"])
    except AccessTokenValidationError as e:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except (KeyError, TypeError, ValueError) as e:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso inválido",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    usuario = uow.usuarios.get_by_id(user_id)
    if usuario is None or not usuario.activo:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def get_current_user_optional(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
    uow: UnitOfWork = Depends(get_uow),
) -> Usuario | None:
    """Si el header Authorization no es un access token válido, devuelve None (no lanza).

    Permite logout con solo `refresh_token` en el body cuando el access ya expiró.
    """
    if creds is None or not creds.credentials:
        return None
    try:
        payload = decode_and_require_access_token(creds.credentials)
        user_id = int(payload["sub"])
    except (AccessTokenValidationError, KeyError, TypeError, ValueError):
        return None
    usuario = uow.usuarios.get_by_id(user_id)
    if usuario is None or not usuario.activo:
        return None
    return usuario
