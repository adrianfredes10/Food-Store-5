from pydantic import BaseModel, ConfigDict


class RefreshTokenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    token_hash: str
    expires_at: str
    revoked_at: str | None = None
