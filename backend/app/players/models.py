from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, CheckConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP
from backend.app.auth.database import Base

class Jugador(Base):
    __tablename__ = "jugadores"

    id = Column(Integer, primary_key=True, index=True)

    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    nacionalidad = Column(String(3))
    altura_cm = Column(Integer)
    brazo_bueno = Column(String(1))  # 'R' o 'L'

    id_creador = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"))

    attr_primer_saque = Column(Integer)
    attr_segundo_saque = Column(Integer)
    attr_resto = Column(Integer)
    attr_derecha = Column(Integer)
    attr_reves = Column(Integer)
    attr_movilidad = Column(Integer)
    attr_consistencia = Column(Integer)
    attr_clutch = Column(Integer)
    attr_fisico = Column(Integer)

    activo = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("brazo_bueno IN ('R','L')"),
        CheckConstraint("attr_primer_saque BETWEEN 1 AND 100"),
        CheckConstraint("attr_segundo_saque BETWEEN 1 AND 100"),
        CheckConstraint("attr_resto BETWEEN 1 AND 100"),
        CheckConstraint("attr_derecha BETWEEN 1 AND 100"),
        CheckConstraint("attr_reves BETWEEN 1 AND 100"),
        CheckConstraint("attr_movilidad BETWEEN 1 AND 100"),
        CheckConstraint("attr_consistencia BETWEEN 1 AND 100"),
        CheckConstraint("attr_clutch BETWEEN 1 AND 100"),
        CheckConstraint("attr_fisico BETWEEN 1 AND 100"),
    )
