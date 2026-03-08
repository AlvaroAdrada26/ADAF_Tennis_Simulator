from typing import Any, Dict, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.simulator.api import run_match
from backend.app.auth.database import get_db
from backend.app.matches.models import Partido, EstadisticaPartido
from backend.app.matches.stats import extract_player_stats


router = APIRouter()
logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Modelos de entrada
# ------------------------------------------------------------
class PlayerData(BaseModel):
    name: str
    id: str
    Primer_Saque: float
    Segundo_Saque: float
    Fisico: float
    Estamina: float
    Consistencia: float
    Clutch: float
    Momentum: float
    Derecha: float
    Reves: float
    Resto: float
    Movilidad: float


class ConfigData(BaseModel):
    best_of: int = 3
    tiebreak: bool = True
    seed: int | None = None
    superficie: str | None = None


class MatchRequest(BaseModel):
    player1: PlayerData
    player2: PlayerData
    config: Optional[ConfigData] = None


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _format_marcador(set_scores: list) -> str:
    """Convierte [(6,4),(3,6),(7,6)] → '6-4, 3-6, 7-6'."""
    return ", ".join(f"{a}-{b}" for a, b in set_scores)


def _estimate_duration_minutes(timeline: list) -> int:
    """Estima la duración del partido en minutos a partir del número de puntos."""
    total_points = len(timeline)
    # Promedio real ≈ 30–40 s por punto; usamos ~35 s
    return max(1, round(total_points * 35 / 60))


def _try_save_match(
    result: Dict[str, Any],
    p1_db_id: int,
    p2_db_id: int,
    config: ConfigData | None,
    db: Session,
) -> int | None:
    """
    Intenta guardar el partido y estadísticas en la BD.
    Devuelve el id del partido creado o None si falla.
    """
    try:
        timeline = result.get("timeline", [])
        set_scores = result.get("set_scores", [])
        winner_id_tag = result.get("winner_id")  # "P1" o "P2"

        id_ganador = p1_db_id if winner_id_tag == "P1" else p2_db_id

        superficie = (config.superficie if config and config.superficie else None)
        formato_sets = (config.best_of if config else 3)
        tiebreak = (config.tiebreak if config else True)

        partido = Partido(
            id_jugador_1=p1_db_id,
            id_jugador_2=p2_db_id,
            id_ganador=id_ganador,
            marcador_final=_format_marcador(set_scores),
            duracion_minutos=_estimate_duration_minutes(timeline),
            superficie=superficie,
            formato_sets=formato_sets,
            tiebreak_ultimo_set=tiebreak,
        )
        db.add(partido)
        db.flush()  # obtener partido.id

        # Extraer estadísticas por jugador
        player_stats = extract_player_stats(timeline)

        for tag, db_id in [("P1", p1_db_id), ("P2", p2_db_id)]:
            s = player_stats[tag]
            est = EstadisticaPartido(
                id_partido=partido.id,
                id_jugador=db_id,
                aces=s["aces"],
                dobles_faltas=s["dobles_faltas"],
                primeros_saques_in=s["primeros_saques_in"],
                primeros_saques_total=s["primeros_saques_total"],
                puntos_ganados_1er_saque=s["puntos_ganados_1er_saque"],
                puntos_ganados_2do_saque=s["puntos_ganados_2do_saque"],
                winners=s["winners"],
                errores_no_forzados=s["errores_no_forzados"],
                puntos_ganados_resto=s["puntos_ganados_resto"],
                total_puntos_ganados=s["total_puntos_ganados"],
                break_points_convertidos=s["break_points_convertidos"],
                break_points_oportunidades=s["break_points_oportunidades"],
            )
            db.add(est)

        db.commit()
        logger.info("Partido %d guardado en BD (P1=%d vs P2=%d)", partido.id, p1_db_id, p2_db_id)
        return partido.id

    except Exception:
        db.rollback()
        logger.exception("No se pudo guardar el partido en BD")
        return None


# ------------------------------------------------------------
# Endpoints API
# ------------------------------------------------------------
@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.post("/simulate_match")
def simulate_match(request: MatchRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Ejecuta una simulación de partido completa y devuelve el resultado detallado
    en formato JSON, incluyendo timeline punto a punto.
    Si los IDs de jugador son válidos (enteros), guarda el partido y las
    estadísticas en la base de datos.
    """
    try:
        result = run_match(
            player1_data=request.player1.model_dump(),
            player2_data=request.player2.model_dump(),
            config=request.config.model_dump(exclude={"superficie"}) if request.config else {},
        )

        timeline = result.get("timeline", [])
        for i, point in enumerate(timeline):
            point["point_index"] = i

        result["timeline"] = timeline

        # ── Guardar en BD si los IDs son enteros válidos ──
        match_id = None
        try:
            p1_db_id = int(request.player1.id)
            p2_db_id = int(request.player2.id)
            match_id = _try_save_match(result, p1_db_id, p2_db_id, request.config, db)
        except (ValueError, TypeError):
            # IDs no numéricos (ej. "P1"/"P2" de pruebas) → no guardar
            pass

        if match_id is not None:
            result["match_db_id"] = match_id

        # ── Incluir estadísticas por jugador en la respuesta ──
        result["player_stats"] = extract_player_stats(timeline)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la simulación: {e}")
