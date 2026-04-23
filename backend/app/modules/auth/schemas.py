from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombre: str = Field(min_length=2, max_length=80)
    apellido: str | None = Field(default=None, max_length=80)


class RegisterResponse(BaseModel):
    id: int
    email: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=2048)


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutRequest(BaseModel):
    """Opcional: revocar un refresh concreto (p. ej. sin access token)."""

    refresh_token: str | None = Field(default=None, max_length=2048)


class MessageResponse(BaseModel):
    message: str


class MeResponse(BaseModel):
    id: int
    nombre: str
    apellido: str | None
    email: str
    roles: list[str]
    created_at: datetime
