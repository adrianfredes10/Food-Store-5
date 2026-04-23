from pydantic import BaseModel, EmailStr, Field


class PagoTarjetaRequest(BaseModel):
    pedido_id: int = Field(ge=1)
    token: str = Field(min_length=1, max_length=512)
    payment_method_id: str = Field(min_length=1, max_length=64)
    payer_email: EmailStr
    installments: int = Field(default=1, ge=1, le=24)


class PagoTarjetaResponse(BaseModel):
    pago_id: int
    estado: str
    mp_status: str | None = None
    mp_payment_id: str | None = None
