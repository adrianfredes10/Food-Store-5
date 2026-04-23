from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Siempre `backend/.env` aunque uvicorn se lance desde otra carpeta (evita GROQ_* vacíos).
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Food Store API"
    debug: bool = False
    database_url: str

    jwt_secret_key: str = Field(
        validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY"),
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias=AliasChoices("JWT_ALGORITHM", "ALGORITHM"))
    access_token_expire_minutes: int = Field(
        default=30,
        validation_alias=AliasChoices("ACCESS_TOKEN_EXPIRE_MINUTES"),
    )
    refresh_token_expire_days: int = Field(
        default=7,
        validation_alias=AliasChoices("REFRESH_TOKEN_EXPIRE_DAYS"),
    )

    # CORS: lista separada por comas (la spec menciona JSON array; en .env es más simple así).
    cors_origins: str = Field(
        default="http://127.0.0.1:5173,http://localhost:5173",
        validation_alias=AliasChoices("CORS_ORIGINS"),
    )

    # Mercado Pago (checkout). Con mock=True no se llama a la API.
    mercadopago_mock: bool = Field(default=True, validation_alias=AliasChoices("MERCADOPAGO_MOCK"))
    mercadopago_access_token: str = Field(
        default="",
        validation_alias=AliasChoices("MERCADOPAGO_ACCESS_TOKEN", "MP_ACCESS_TOKEN"),
    )
    public_app_url: str = Field(
        default="http://localhost:8000",
        validation_alias=AliasChoices("PUBLIC_APP_URL"),
    )

    # Groq solo genera texto (prompt). La imagen se resuelve vía URL pública (ver integrations).
    groq_api_key: str = Field(default="", validation_alias=AliasChoices("GROQ_API_KEY"))
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        validation_alias=AliasChoices("GROQ_MODEL"),
    )
    producto_imagen_auto: bool = Field(
        default=False,
        validation_alias=AliasChoices("PRODUCTO_IMAGEN_AUTO"),
    )

    def cors_origins_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
