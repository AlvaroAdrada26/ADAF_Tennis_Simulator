"""
Modelos SQLAlchemy para las tablas `torneos` y `torneo_partidos`.
"""

from sqlalchemy import (
    Boolean, Column, Integer, String, ForeignKey, CheckConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm import relationship

from backend.app.auth.database import Base


class Torneo(Base):
    __tablename__ = "torneos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    id_usuario_creador = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    superficie = Column(String(20))
    formato_sets = Column(Integer, default=3)
    tiebreak_ultimo_set = Column(Boolean, default=True)
    num_jugadores = Column(Integer, nullable=False)
    id_ganador = Column(Integer, ForeignKey("jugadores.id", ondelete="SET NULL"), nullable=True)
    ids_jugadores = Column(String, nullable=True)   # IDs separados por coma: "1,3,5,7"
    ids_partidos = Column(String, nullable=True)    # IDs separados por coma: "10,11,12"
    completado = Column(Boolean, default=False)
    fecha_creado = Column(TIMESTAMP(timezone=True), server_default=func.now())
    activo = Column(Boolean, default=True)

    partidos = relationship("TorneoPartido", back_populates="torneo", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("superficie IN ('Dura','Arcilla','Hierba')", name="ck_torneo_superficie"),
        CheckConstraint("formato_sets IN (1,3,5)", name="ck_torneo_formato"),
        CheckConstraint("num_jugadores IN (4,8,16)", name="ck_torneo_num_jugadores"),
    )


class TorneoPartido(Base):
    __tablename__ = "torneo_partidos"

    id = Column(Integer, primary_key=True, index=True)
    id_torneo = Column(Integer, ForeignKey("torneos.id", ondelete="CASCADE"))
    id_partido = Column(Integer, ForeignKey("partidos.id", ondelete="CASCADE"), nullable=True)
    ronda = Column(Integer, nullable=False)
    posicion = Column(Integer, nullable=False)
    id_jugador_1 = Column(Integer, ForeignKey("jugadores.id", ondelete="CASCADE"), nullable=True)
    id_jugador_2 = Column(Integer, ForeignKey("jugadores.id", ondelete="CASCADE"), nullable=True)
    id_ganador = Column(Integer, ForeignKey("jugadores.id", ondelete="SET NULL"), nullable=True)
    completado = Column(Boolean, default=False)

    torneo = relationship("Torneo", back_populates="partidos")
