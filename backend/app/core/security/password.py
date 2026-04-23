from passlib.context import CryptContext

# Spec v5: bcrypt cost factor ≥ 12
_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(plain: str) -> str:
    return _context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _context.verify(plain, hashed)
