import hashlib

from sqlmodel import Session, select

from app.modules.usuarios.model import Usuario


def hash_refresh_token_plain(plain: str) -> str:
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


class AuthRepository:
    __slots__ = ("_session",)

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_usuario_por_email(self, email: str) -> Usuario | None:
        stmt = select(Usuario).where(Usuario.email == email)
        return self._session.exec(stmt).first()

    def add_usuario(self, usuario: Usuario) -> Usuario:
        self._session.add(usuario)
        return usuario
