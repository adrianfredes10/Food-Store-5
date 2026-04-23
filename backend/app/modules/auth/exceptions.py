class ErrorAuth(Exception):
    """Base errores de autenticación / registro."""


class EmailDuplicadoError(ErrorAuth):
    def __init__(self, email: str) -> None:
        super().__init__(f"El email ya está registrado: {email}")
        self.email = email


class CredencialesInvalidasError(ErrorAuth):
    def __init__(self) -> None:
        super().__init__("Email o contraseña incorrectos")


class RefreshTokenInvalidoError(ErrorAuth):
    def __init__(self) -> None:
        super().__init__("Refresh token inválido o expirado")


class RefreshTokenRevocadoError(ErrorAuth):
    def __init__(self) -> None:
        super().__init__("Refresh token revocado")


class UsuarioInactivoError(ErrorAuth):
    def __init__(self) -> None:
        super().__init__("Usuario inactivo")


class DemasiadosIntentosLoginError(ErrorAuth):
    def __init__(self) -> None:
        super().__init__("Demasiados intentos fallidos. Reintentá en unos minutos.")
