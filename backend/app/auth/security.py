"""
Utilidades de seguridad: hash de contraseñas y JWT tokens.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# -- Configuracion --
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "adaf-tennis-super-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 dias

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -- Password hashing --
def hash_password(plain: str) -> str:
    """Genera un hash bcrypt de la contraseña en texto plano."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica que la contraseña plana coincida con el hash."""
    return pwd_context.verify(plain, hashed)


# -- JWT --
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un JWT firmado con los datos proporcionados."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica y valida un JWT. Retorna None si es inválido o expirado."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
