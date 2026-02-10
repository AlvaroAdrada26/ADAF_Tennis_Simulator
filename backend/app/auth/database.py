"""
Configuración de la base de datos PostgreSQL.

Usa variables de entorno (o .env) para las credenciales.
Si no existen, se usan valores por defecto válidos para desarrollo local.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:root@localhost:5432/adaf"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia FastAPI para obtener una sesión de BD."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
