"""
Modelo SQLAlchemy para la tabla `usuarios`.

Esquema:
  id SERIAL PRIMARY KEY
  username VARCHAR(50)  UNIQUE NOT NULL
  email    VARCHAR(100) UNIQUE NOT NULL
  password_hash VARCHAR(255) NOT NULL
  nombre VARCHAR(100) NOT NULL
  apellido VARCHAR(100)
  nacionalidad VARCHAR(50)
  genero VARCHAR(20)
  foto_perfil_url VARCHAR(255)
  activo BOOLEAN DEFAULT TRUE
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from backend.app.auth.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=True)
    nacionalidad = Column(String(50), nullable=True)
    genero = Column(String(20), nullable=True)
    foto_perfil_url = Column(String(255), nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Usuario(id={self.id}, username='{self.username}')>"
