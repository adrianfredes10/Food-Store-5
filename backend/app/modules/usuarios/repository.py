from sqlmodel import Session, select

from app.core.repository.base_repository import BaseRepository
from app.modules.usuarios.model import Rol, Usuario, UsuarioRol


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Usuario)

    def list_codigos_roles_activos(self, usuario_id: int) -> set[str]:
        stmt = (
            select(Rol)
            .join(UsuarioRol, UsuarioRol.rol_codigo == Rol.codigo)
            .where(UsuarioRol.usuario_id == usuario_id, Rol.activo == True)  # noqa: E712
        )
        return {r.codigo for r in self._session.exec(stmt).all()}
