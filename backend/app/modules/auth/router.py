import os

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.uow.unit_of_work import UnitOfWork
from app.core.rate_limit import limiter
from app.deps.uow import get_uow
from app.deps.auth import get_current_user, get_current_user_optional
from app.modules.auth.exceptions import (
    CredencialesInvalidasError,
    DemasiadosIntentosLoginError,
    EmailDuplicadoError,
    ErrorAuth,
    RefreshTokenInvalidoError,
    RefreshTokenRevocadoError,
    UsuarioInactivoError,
)
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.modules.auth.service import AuthService
from app.modules.usuarios.model import Usuario

router = APIRouter(prefix="/auth", tags=["auth"])

_auth_service = AuthService()

_rl_login = (
    (lambda f: f)
    if os.getenv("PYTEST_DISABLE_RATE_LIMIT", "").lower() in ("1", "true", "yes")
    else limiter.limit("5 per 15 minutes")
)


def _map_auth_error(exc: ErrorAuth) -> HTTPException:
    if isinstance(exc, EmailDuplicadoError):
        return HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, CredencialesInvalidasError):
        return HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    if isinstance(exc, (RefreshTokenInvalidoError, RefreshTokenRevocadoError)):
        return HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    if isinstance(exc, UsuarioInactivoError):
        return HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, DemasiadosIntentosLoginError):
        return HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))
    return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> RegisterResponse:
    try:
        return _auth_service.register(uow, body)
    except ErrorAuth as e:
        raise _map_auth_error(e) from e


@router.get("/me", response_model=MeResponse)
def me(
    usuario: Usuario = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MeResponse:
    if usuario.id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida")
    roles = sorted(uow.usuarios.list_codigos_roles_activos(usuario.id))
    return MeResponse(
        id=usuario.id,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        roles=roles,
        created_at=usuario.created_at,
    )


@router.post("/login", response_model=LoginResponse)
@_rl_login
def login(
    request: Request,
    body: LoginRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> LoginResponse:
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent")
    try:
        return _auth_service.login(uow, body, client_ip=ip, user_agent=ua)
    except ErrorAuth as e:
        raise _map_auth_error(e) from e


@router.post("/refresh", response_model=RefreshResponse)
def refresh_token(
    body: RefreshRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> RefreshResponse:
    # verifico el token antes de continuar
    try:
        return _auth_service.refresh(uow, body)
    except ErrorAuth as e:
        raise _map_auth_error(e) from e


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    body: LogoutRequest,
    current_user: Usuario | None = Depends(get_current_user_optional),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    refresh_plain = (body.refresh_token or "").strip() or None
    if current_user is None and refresh_plain is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Enviá Authorization: Bearer <access> o refresh_token en el body",
        )
    try:
        _auth_service.logout(
            uow,
            usuario_id=current_user.id if current_user is not None else None,
            refresh_token_plain=refresh_plain,
        )
    except ErrorAuth as e:
        raise _map_auth_error(e) from e
