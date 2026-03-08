"""
Modelos SQLAlchemy para las tablas `partidos` y `estadisticas_partido`.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, CheckConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm import relationship

from backend.app.auth.database import Base


class Partido(Base):
    __tablename__ = "partidos"

    id = Column(Integer, primary_key=True, index=True)

    # Quién jugó
    id_jugador_1 = Column(Integer, ForeignKey("jugadores.id", ondelete="CASCADE"))
    id_jugador_2 = Column(Integer, ForeignKey("jugadores.id", ondelete="CASCADE"))
    id_ganador = Column(Integer, ForeignKey("jugadores.id", ondelete="CASCADE"))

    # Detalles del Partido
    marcador_final = Column(String(50), nullable=False)  # Ej: "6-4, 6-2, 7-6"
    duracion_minutos = Column(Integer)
    fecha_jugado = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Configuración
    superficie = Column(String(20))
    formato_sets = Column(Integer)
    tiebreak_ultimo_set = Column(Boolean, default=True)

    activo = Column(Boolean, default=True)

    # Relaciones
    estadisticas = relationship("EstadisticaPartido", back_populates="partido", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("superficie IN ('Dura','Arcilla','Hierba','Moqueta')", name="ck_superficie"),
        CheckConstraint("formato_sets IN (1,3,5)", name="ck_formato_sets"),
    )


class EstadisticaPartido(Base):
    __tablename__ = "estadisticas_partido"

    id = Column(Integer, primary_key=True, index=True)

    # Relaciones
    id_partido = Column(Integer, ForeignKey("partidos.id", ondelete="CASCADE"))
    id_jugador = Column(Integer, ForeignKey("jugadores.id", ondelete="CASCADE"))

    # BLOQUE A: SERVICIO
    aces = Column(Integer, default=0)
    dobles_faltas = Column(Integer, default=0)

    primeros_saques_in = Column(Integer, default=0)
    primeros_saques_total = Column(Integer, default=0)

    puntos_ganados_1er_saque = Column(Integer, default=0)
    puntos_ganados_2do_saque = Column(Integer, default=0)

    # BLOQUE B: JUEGO / RESTO
    winners = Column(Integer, default=0)
    errores_no_forzados = Column(Integer, default=0)

    puntos_ganados_resto = Column(Integer, default=0)
    total_puntos_ganados = Column(Integer, default=0)

    # BLOQUE C: BREAK POINTS
    break_points_convertidos = Column(Integer, default=0)
    break_points_oportunidades = Column(Integer, default=0)

    # Relación inversa
    partido = relationship("Partido", back_populates="estadisticas")

    __table_args__ = (
        CheckConstraint("aces >= 0", name="ck_aces"),
        CheckConstraint("dobles_faltas >= 0", name="ck_dobles_faltas"),
        CheckConstraint("primeros_saques_in <= primeros_saques_total", name="ck_saques_in"),
        CheckConstraint(
            "break_points_convertidos <= break_points_oportunidades",
            name="ck_break_points",
        ),
    )
