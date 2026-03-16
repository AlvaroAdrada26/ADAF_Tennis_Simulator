"""
API routes para consulta y guardado de partidos y estadísticas.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.auth.database import get_db
from backend.app.matches.models import Partido, EstadisticaPartido
from backend.app.matches.stats import extract_player_stats
from backend.app.players.models import Jugador

router = APIRouter(prefix="/matches", tags=["matches"])
logger = logging.getLogger(__name__)


# ─── Schemas de entrada para guardar partido ───────────────────
class SaveMatchConfig(BaseModel):
    surface: str = "Dura"
    best_of: int = 3
    tiebreak: bool = True


class SaveMatchRequest(BaseModel):
    """Datos que envía el frontend tras finalizar la simulación."""
    id_jugador_1: int              # DB id del jugador 1
    id_jugador_2: int              # DB id del jugador 2
    id_usuario_creador: Optional[int] = None
    winner_id: str                 # "P1" o "P2"
    set_scores: List[List[int]]    # [[6,4],[3,6],[7,5]]
    config: SaveMatchConfig
    timeline: List[Dict[str, Any]] # timeline completa de puntos


def _build_marcador(set_scores: List[List[int]]) -> str:
    """Genera marcador legible: '6-4, 3-6, 7-5'."""
    return ", ".join(f"{s[0]}-{s[1]}" for s in set_scores)


# ─── POST  /api/matches  — Guardar partido ─────────────────────
@router.post("/")
def save_match(body: SaveMatchRequest, db: Session = Depends(get_db)):
    """
    Guarda un partido recién simulado en la base de datos.
    Crea 1 fila en `partidos` y 2 filas en `estadisticas_partido`.
    """
    # Validar que los jugadores existen
    j1 = db.query(Jugador).filter(Jugador.id == body.id_jugador_1).first()
    j2 = db.query(Jugador).filter(Jugador.id == body.id_jugador_2).first()
    if not j1 or not j2:
        raise HTTPException(status_code=404, detail="Uno de los jugadores no existe en la BD")

    # Determinar ganador (id de BD)
    id_ganador = body.id_jugador_1 if body.winner_id == "P1" else body.id_jugador_2

    # Crear el partido
    partido = Partido(
        id_jugador_1=body.id_jugador_1,
        id_jugador_2=body.id_jugador_2,
        id_ganador=id_ganador,
        id_usuario_creador=body.id_usuario_creador,
        marcador_final=_build_marcador(body.set_scores),
        duracion_minutos=None,  # El simulador no calcula duración real
        superficie=body.config.surface,
        formato_sets=body.config.best_of,
        tiebreak_ultimo_set=body.config.tiebreak,
    )
    db.add(partido)
    db.flush()  # Para obtener partido.id

    # Calcular y guardar estadísticas de cada jugador
    all_stats = extract_player_stats(body.timeline)
    for player_tag, db_player_id in [("P1", body.id_jugador_1), ("P2", body.id_jugador_2)]:
        stats = all_stats[player_tag]
        stat_row = EstadisticaPartido(
            id_partido=partido.id,
            id_jugador=db_player_id,
            id_usuario=body.id_usuario_creador,
            **stats,
        )
        db.add(stat_row)

    db.commit()
    db.refresh(partido)

    return {
        "ok": True,
        "partido_id": partido.id,
        "marcador": partido.marcador_final,
        "ganador_id": id_ganador,
    }


# ─── GET  /api/matches/{id}  — Consultar partido ───────────────
@router.get("/{match_id}")
def get_match_summary(match_id: int, db: Session = Depends(get_db)):
    """
    Devuelve toda la info de un partido + estadísticas de ambos jugadores.
    """
    partido = db.query(Partido).filter(Partido.id == match_id, Partido.activo == True).first()
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    j1 = db.query(Jugador).filter(Jugador.id == partido.id_jugador_1).first()
    j2 = db.query(Jugador).filter(Jugador.id == partido.id_jugador_2).first()
    if not j1 or not j2:
        raise HTTPException(status_code=404, detail="Jugadores no encontrados")

    stats = (
        db.query(EstadisticaPartido)
        .filter(EstadisticaPartido.id_partido == match_id)
        .all()
    )

    stats_j1 = next((s for s in stats if s.id_jugador == partido.id_jugador_1), None)
    stats_j2 = next((s for s in stats if s.id_jugador == partido.id_jugador_2), None)

    def player_info(j):
        return {
            "id": j.id,
            "nombre": j.nombre,
            "apellido": j.apellido,
            "nombre_completo": f"{j.nombre} {j.apellido}",
            "nacionalidad": j.nacionalidad,
            "brazo_bueno": j.brazo_bueno,
        }

    def stat_block(s):
        if not s:
            return None
        pct_1er = round(s.primeros_saques_in / s.primeros_saques_total * 100) if s.primeros_saques_total else 0
        pct_bp = round(s.break_points_convertidos / s.break_points_oportunidades * 100) if s.break_points_oportunidades else 0
        return {
            "aces": s.aces,
            "dobles_faltas": s.dobles_faltas,
            "primeros_saques_in": s.primeros_saques_in,
            "primeros_saques_total": s.primeros_saques_total,
            "pct_primer_saque": pct_1er,
            "puntos_ganados_1er_saque": s.puntos_ganados_1er_saque,
            "puntos_ganados_2do_saque": s.puntos_ganados_2do_saque,
            "winners": s.winners,
            "errores_no_forzados": s.errores_no_forzados,
            "puntos_ganados_resto": s.puntos_ganados_resto,
            "total_puntos_ganados": s.total_puntos_ganados,
            "break_points_convertidos": s.break_points_convertidos,
            "break_points_oportunidades": s.break_points_oportunidades,
            "pct_break_points": pct_bp,
        }

    superficie_icons = {
        "Dura": "🏟️",
        "Tierra": "🧱",
        "Hierba": "🌿"
    }

    return {
        "partido": {
            "id": partido.id,
            "marcador_final": partido.marcador_final,
            "duracion_minutos": partido.duracion_minutos,
            "fecha_jugado": partido.fecha_jugado.isoformat() if partido.fecha_jugado else None,
            "superficie": partido.superficie,
            "superficie_icon": superficie_icons.get(partido.superficie, ""),
            "formato_sets": partido.formato_sets,
            "tiebreak_ultimo_set": partido.tiebreak_ultimo_set,
            "id_ganador": partido.id_ganador,
        },
        "jugador_1": player_info(j1),
        "jugador_2": player_info(j2),
        "stats_jugador_1": stat_block(stats_j1),
        "stats_jugador_2": stat_block(stats_j2),
    }
