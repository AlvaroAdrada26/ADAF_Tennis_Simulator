"""
Modelos SQLAlchemy para las tablas `partidos` y `estadisticas_partido`.
"""

from sqlalchemy import (
    Boolean, Column, Integer, String, ForeignKey, CheckConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP

from backend.app.auth.database import Base


class Partido(Base):
    __tablename__ = "partidos"

    id = Column(Integer, primary_key=True, index=True)

    id_jugador_1 = Column(Integer, ForeignKey("jugadores.id", ondelete="CASCADE"))
    id_jugador_2 = Column(Integer, ForeignKey("jugadores.id", ondelete="CASCADE"))
    id_ganador = Column(Integer, ForeignKey("jugadores.id", ondelete="CASCADE"))
    id_usuario_creador = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)

    marcador_final = Column(String(50), nullable=False)
    duracion_minutos = Column(Integer)
    fecha_jugado = Column(TIMESTAMP(timezone=True), server_default=func.now())

    superficie = Column(String(20))
    formato_sets = Column(Integer)
    tiebreak_ultimo_set = Column(Boolean, default=True)

    activo = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint("superficie IN ('Dura','Tierra','Hierba')"),
        CheckConstraint("formato_sets IN (1,3,5)"),
    )


class EstadisticaPartido(Base):
    __tablename__ = "estadisticas_partido"

    id = Column(Integer, primary_key=True, index=True)

    id_partido = Column(Integer, ForeignKey("partidos.id", ondelete="CASCADE"))
    id_jugador = Column(Integer, ForeignKey("jugadores.id", ondelete="CASCADE"))

    # Servicio
    aces = Column(Integer, default=0)
    dobles_faltas = Column(Integer, default=0)
    primeros_saques_in = Column(Integer, default=0)
    primeros_saques_total = Column(Integer, default=0)
    puntos_ganados_1er_saque = Column(Integer, default=0)
    puntos_ganados_2do_saque = Column(Integer, default=0)

    # Juego
    winners = Column(Integer, default=0)
    errores_no_forzados = Column(Integer, default=0)
    puntos_ganados_resto = Column(Integer, default=0)
    total_puntos_ganados = Column(Integer, default=0)

    # Break points
    break_points_convertidos = Column(Integer, default=0)
    break_points_oportunidades = Column(Integer, default=0)

    __table_args__ = (
        CheckConstraint("aces >= 0"),
        CheckConstraint("dobles_faltas >= 0"),
        CheckConstraint("primeros_saques_in <= primeros_saques_total"),
        CheckConstraint("break_points_convertidos <= break_points_oportunidades"),
    )
