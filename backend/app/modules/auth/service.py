"""Lógica de registro, login, refresh y logout. Sin commit (lo hace get_uow)."""

# TODO: agregar logs para debuggear errores en produccion

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.security.password import hash_password, verify_password
from app.core.security.jwt_tokens import create_access_token
from app.core.uow.unit_of_work import UnitOfWork
from app.modules.auth.exceptions import (
    CredencialesInvalidasError,
    EmailDuplicadoError,
    RefreshTokenInvalidoError,
    RefreshTokenRevocadoError,
    UsuarioInactivoError,
)
from app.modules.auth.login_throttle import (
    assert_ip_puede_intentar_login,
    limpiar_fallos_ip,
    registrar_login_fallido,
)
from app.modules.auth.repository import hash_refresh_token_plain
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.modules.refreshtokens.model import RefreshToken
from app.modules.usuarios.model import Rol, Usuario, UsuarioRol


def _dt_utc(dt: datetime) -> datetime:
    """SQLite puede devolver datetimes naive; normaliza a UTC consciente de zona."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class AuthService:
    def register(self, uow: UnitOfWork, data: RegisterRequest) -> RegisterResponse:
        # 1. verifico que el email no esté registrado ya
        repo = uow.auth
        if repo.get_usuario_por_email(data.email) is not None:
            raise EmailDuplicadoError(data.email)

        # 2. creo el usuario con la contraseña hasheada
        usuario = Usuario(
            email=data.email,
            hashed_password=hash_password(data.password),
            nombre=data.nombre,
            apellido=data.apellido,
            activo=True,
        )
        repo.add_usuario(usuario)
        uow.flush()
        if usuario.id is None:
            raise RuntimeError("No se obtuvo id de usuario tras flush")
        # 3. le asigno el rol CLIENT por defecto si existe
        if uow.session.get(Rol, "CLIENT") is not None:
            uow.session.add(UsuarioRol(usuario_id=usuario.id, rol_codigo="CLIENT"))
        return RegisterResponse(id=usuario.id, email=usuario.email)

    def login(
        self,
        uow: UnitOfWork,
        data: LoginRequest,
        *,
        client_ip: str,
        user_agent: str | None,
    ) -> LoginResponse:
        assert_ip_puede_intentar_login(client_ip)
        repo = uow.auth
        usuario = repo.get_usuario_por_email(data.email)
        if usuario is None or not verify_password(data.password, usuario.hashed_password):
            registrar_login_fallido(client_ip)
            raise CredencialesInvalidasError()
        if not usuario.activo:
            raise UsuarioInactivoError()

        limpiar_fallos_ip(client_ip)

        plain_refresh = secrets.token_urlsafe(48)
        token_hash = hash_refresh_token_plain(plain_refresh)
        now = datetime.now(timezone.utc)
        expires_refresh = now + timedelta(days=settings.refresh_token_expire_days)

        # guardo el refresh token en la base
        row = RefreshToken(
            usuario_id=usuario.id,
            token_hash=token_hash,
            expires_at=expires_refresh,
            user_agent=user_agent,
            ip_origen=client_ip,
        )
        uow.refreshtokens.add(row)
        uow.flush()

        access = create_access_token(subject_user_id=usuario.id)
        return LoginResponse(
            access_token=access,
            refresh_token=plain_refresh,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    def refresh(self, uow: UnitOfWork, data: RefreshRequest) -> RefreshResponse:
        # 1. busco el token en la base
        token_hash = hash_refresh_token_plain(data.refresh_token)
        row = uow.refreshtokens.get_by_token_hash_for_update(token_hash)
        if row is None:
            raise RefreshTokenInvalidoError()

        # 2. valido que no esté revocado ni expirado
        now = datetime.now(timezone.utc)
        if row.revoked_at is not None:
            raise RefreshTokenRevocadoError()
        if _dt_utc(row.expires_at) <= now:
            raise RefreshTokenInvalidoError()

        usuario = uow.usuarios.get_by_id(row.usuario_id)
        if usuario is None or not usuario.activo:
            raise UsuarioInactivoError()

        # 3. revoco el token viejo (rotación)
        row.revoked_at = now

        plain_refresh = secrets.token_urlsafe(48)
        nuevo_hash = hash_refresh_token_plain(plain_refresh)
        expires_refresh = now + timedelta(days=settings.refresh_token_expire_days)

        # guardo el refresh token nuevo en la base
        nuevo = RefreshToken(
            usuario_id=usuario.id,
            token_hash=nuevo_hash,
            expires_at=expires_refresh,
            user_agent=row.user_agent,
            ip_origen=row.ip_origen,
        )
        uow.refreshtokens.add(nuevo)
        uow.flush()

        access = create_access_token(subject_user_id=usuario.id)
        return RefreshResponse(
            access_token=access,
            refresh_token=plain_refresh,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    def logout(
        self,
        uow: UnitOfWork,
        *,
        usuario_id: int | None = None,
        refresh_token_plain: str | None = None,
    ) -> None:
        if usuario_id is not None:
            uow.refreshtokens.revocar_todos_activos_por_usuario(usuario_id)
        if refresh_token_plain:
            self._revocar_refresh_por_plain(uow, refresh_token_plain)

    def _revocar_refresh_por_plain(self, uow: UnitOfWork, refresh_token_plain: str) -> None:
        token_hash = hash_refresh_token_plain(refresh_token_plain)
        row = uow.refreshtokens.get_by_token_hash(token_hash)
        if row is None:
            raise RefreshTokenInvalidoError()
        if row.revoked_at is not None:
            return
        row.revoked_at = datetime.now(timezone.utc)
