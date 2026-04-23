import logging
from decimal import Decimal

from sqlalchemy import func, text
from sqlmodel import Session, select

from app.core.db import get_engine
from app.core.security.password import hash_password
from app.modules.pagos.model import FormaPago
from app.modules.pedidos.model import EstadoPedido
from app.modules.productos.model import Categoria, Producto
from app.modules.usuarios.model import Rol, Usuario, UsuarioRol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_roles(session: Session) -> None:
    roles = [
        Rol(codigo="ADMIN", nombre="Administrador", descripcion="Acceso total al sistema"),
        Rol(codigo="STOCK", nombre="Gestor de Stock", descripcion="Gestión de productos y existencias"),
        Rol(codigo="PEDIDOS", nombre="Gestor de Pedidos", descripcion="Seguimiento y cambio de estados de pedidos"),
        Rol(codigo="CLIENT", nombre="Cliente", descripcion="Usuario final que realiza pedidos"),
    ]
    for r in roles:
        existing = session.get(Rol, r.codigo)
        if not existing:
            session.add(r)
            logger.info(f"Rol {r.codigo} creado.")


def seed_estados_pedido(session: Session) -> None:
    estados = [
        EstadoPedido(codigo="PENDIENTE", nombre="Pendiente", orden=1, es_terminal=False),
        EstadoPedido(codigo="CONFIRMADO", nombre="Confirmado", orden=2, es_terminal=False),
        EstadoPedido(codigo="EN_PREP", nombre="En Preparación", orden=3, es_terminal=False),
        EstadoPedido(codigo="EN_CAMINO", nombre="En Camino", orden=4, es_terminal=False),
        EstadoPedido(codigo="ENTREGADO", nombre="Entregado", orden=5, es_terminal=True),
        EstadoPedido(codigo="CANCELADO", nombre="Cancelado", orden=6, es_terminal=True),
    ]
    for e in estados:
        existing = session.get(EstadoPedido, e.codigo)
        if not existing:
            session.add(e)
            logger.info(f"Estado de pedido {e.codigo} creado.")


def seed_formapago(session: Session) -> None:
    formas = [
        FormaPago(codigo="MERCADOPAGO", nombre="Mercado Pago", habilitado=True),
        FormaPago(codigo="EFECTIVO", nombre="Efectivo", habilitado=True),
        FormaPago(codigo="TRANSFERENCIA", nombre="Transferencia Bancaria", habilitado=True),
    ]
    for f in formas:
        existing = session.get(FormaPago, f.codigo)
        if not existing:
            session.add(f)
            logger.info(f"Forma de Pago {f.codigo} creada.")


def seed_admin(session: Session) -> None:
    email = "admin@foodstore.com"
    stmt = select(Usuario).where(Usuario.email == email)
    admin = session.exec(stmt).first()

    if not admin:
        admin = Usuario(
            email=email,
            hashed_password=hash_password("Admin1234!"),
            nombre="Admin",
            apellido="FoodStore",
            activo=True,
        )
        session.add(admin)
        session.flush()
        logger.info(f"Usuario admin {email} creado.")

        # Asignar rol ADMIN
        vinculo = UsuarioRol(usuario_id=admin.id, rol_codigo="ADMIN")
        session.add(vinculo)
        logger.info("Rol ADMIN asignado al usuario admin.")


def run_seed() -> None:
    engine = get_engine()
    with Session(engine) as session:
        seed_roles(session)
        seed_estados_pedido(session)
        seed_formapago(session)
        seed_admin(session)
        session.commit()
        logger.info("Seeding completado exitosamente.")


def seed_demo_catalog_if_empty(session: Session) -> None:
    """Inserta categoría y productos gourmet si no hay suficientes productos."""
    stmt = select(func.count()).select_from(Producto)
    count_val = session.exec(stmt).one()
    total = int(count_val[0]) if isinstance(count_val, tuple) else int(count_val)
    
    # Si ya hay 4 o más productos, asumimos que ya está sembrado
    if total >= 4:
        return

    # Si hay productos viejos pero son pocos, los borramos para sembrar el catálogo gourmet
    if total > 0:
        logger.info("Limpiando catálogo antiguo para sembrar catálogo gourmet...")
        # No usamos delete masivo para evitar problemas de FK si no está configurado CASCADE
        # Pero como es dev, borramos todo
        session.execute(text("DELETE FROM productos"))
        session.execute(text("DELETE FROM categorias"))
        session.commit()

    logger.info("Sembrando Catálogo Gourmet Exclusivo...")
    
    cat_burgers = Categoria(nombre="Burgers & Carnes", descripcion="Selección de carnes premium")
    cat_med = Categoria(nombre="Mediterránea", descripcion="Frescura y tradición")
    session.add(cat_burgers)
    session.add(cat_med)
    session.flush()

    productos = [
        Producto(
            categoria_id=cat_burgers.id,
            nombre="Truffled Black Burger",
            descripcion="Carne madurada 45 días, trufa negra fresca, queso brie fondant y pan de carbón activado.",
            precio=Decimal("18500.00"),
            stock_cantidad=50,
            disponible=True,
            activo=True,
            # URLs públicas (Unsplash); antes /images/*.png no existía en public/ → imagen rota
            imagen_url="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&auto=format&fit=crop&q=80",
        ),
        Producto(
            categoria_id=cat_burgers.id,
            nombre="Wagyu Gold Steak",
            descripcion="Corte Wagyu A5 con costra de sal ahumada y reducción de vino Malbec reserva.",
            precio=Decimal("45000.00"),
            stock_cantidad=20,
            disponible=True,
            activo=True,
            imagen_url="https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=800&auto=format&fit=crop&q=80",
        ),
        Producto(
            categoria_id=cat_med.id,
            nombre="Burrata & Pesto D'Oro",
            descripcion="Burrata pugliese, tomates cherry confitados en oliva extra virgen y pesto de pistachos.",
            precio=Decimal("14200.00"),
            stock_cantidad=40,
            disponible=True,
            activo=True,
            imagen_url="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800&auto=format&fit=crop&q=80",
        ),
        Producto(
            categoria_id=cat_med.id,
            nombre="Artisan Prosciutto Pizza",
            descripcion="Masa de larga fermentación, prosciutto di parma, rúcula selvática y escamas de Grana Padano.",
            precio=Decimal("16800.00"),
            stock_cantidad=30,
            disponible=True,
            activo=True,
            imagen_url="https://images.unsplash.com/photo-1513104890138-7c749659a591?w=800&auto=format&fit=crop&q=80",
        ),
    ]
    for p in productos:
        session.add(p)
    
    logger.info("Catálogo Gourmet Sembrado con éxito (4 productos).")


if __name__ == "__main__":
    run_seed()
    engine = get_engine()
    with Session(engine) as session:
        seed_demo_catalog_if_empty(session)
        session.commit()
    logger.info("Módulo seed: catálogo demo verificado.")
