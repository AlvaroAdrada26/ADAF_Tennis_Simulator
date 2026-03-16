import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.simulator.api import run_match
from backend.app.auth.database import get_db
from backend.app.auth.security import decode_access_token
from backend.app.matches.models import Partido, EstadisticaPartido
from backend.app.matches.stats import extract_player_stats

router = APIRouter()
logger = logging.getLogger(__name__)
bearing = HTTPBearer(auto_error=False)


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
# Normalizar nombres de superficie al valor que acepta el CHECK de la BD
# La BD fue creada con ('Dura', 'Arcilla', 'Hierba')
_SUPERFICIE_NORM: dict[str, str] = {
    "dura":    "Dura",
    "hard":    "Dura",
    "tierra":  "Arcilla",
    "arcilla": "Arcilla",
    "clay":    "Arcilla",
    "hierba":  "Hierba",
    "grass":   "Hierba",
}
_VALID_SUPERFICIES = {"Dura", "Arcilla", "Hierba"}


def _normalize_superficie(raw: str | None) -> str | None:
    """Mapea cualquier variante de nombre de superficie al valor canónico de la BD."""
    if raw is None:
        return None
    canon = _SUPERFICIE_NORM.get(raw.lower())
    if canon:
        return canon
    # Si ya es un valor válido (mayúscula correcta) devuélvelo tal cual
    if raw in _VALID_SUPERFICIES:
        return raw
    # Valor desconocido → None para evitar violación del CHECK
    logger.warning("Superficie desconocida '%s', se guardará como NULL", raw)
    return None


def _format_marcador(set_scores: list) -> str:
    return ", ".join(f"{a}-{b}" for a, b in set_scores)


def _estimate_duration_minutes(timeline: list) -> int:
    """Estima duración aproximada: ~35 s por punto."""
    return max(1, round(len(timeline) * 35 / 60))


def _try_save_match(
    result: Dict[str, Any],
    p1_db_id: int,
    p2_db_id: int,
    config: Optional[ConfigData],
    db: Session,
    id_usuario_creador: Optional[int] = None,
) -> Optional[int]:
    """
    Intenta guardar el partido y sus estadísticas en la BD.
    Devuelve el id del partido creado, o None si falla.
    """
    try:
        timeline = result.get("timeline", [])
        set_scores = result.get("set_scores", [])
        winner_id_tag = result.get("winner_id")  # "P1" o "P2"

        id_ganador = p1_db_id if winner_id_tag == "P1" else p2_db_id
        superficie = _normalize_superficie(config.superficie if config else None)
        formato_sets = config.best_of if config else 3
        tiebreak = config.tiebreak if config else True

        partido = Partido(
            id_jugador_1=p1_db_id,
            id_jugador_2=p2_db_id,
            id_ganador=id_ganador,
            id_usuario_creador=id_usuario_creador,
            marcador_final=_format_marcador(set_scores),
            duracion_minutos=_estimate_duration_minutes(timeline),
            superficie=superficie,
            formato_sets=formato_sets,
            tiebreak_ultimo_set=tiebreak,
        )
        db.add(partido)
        db.flush()  # obtener partido.id

        player_stats = extract_player_stats(timeline)
        for tag, db_id in [("P1", p1_db_id), ("P2", p2_db_id)]:
            s = player_stats[tag]
            est = EstadisticaPartido(
                id_partido=partido.id,
                id_jugador=db_id,
                id_usuario=id_usuario_creador,
                **s,
            )
            db.add(est)

        db.commit()
        logger.info(
            "Partido %d guardado automáticamente (P1=%d vs P2=%d, user=%s)",
            partido.id, p1_db_id, p2_db_id, id_usuario_creador,
        )
        return partido.id

    except Exception:
        db.rollback()
        logger.exception("No se pudo guardar el partido automáticamente")
        return None


# ------------------------------------------------------------
# Endpoints API
# ------------------------------------------------------------
@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.post("/simulate_match")
def simulate_match(
    request: MatchRequest,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearing),
) -> Dict[str, Any]:
    """
    Ejecuta una simulación de partido completa y devuelve el resultado detallado
    en formato JSON, incluyendo timeline punto a punto.

    Si los IDs de jugador son enteros válidos (jugadores de BD), guarda el partido
    automáticamente y devuelve `match_db_id` en la respuesta.
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

        # ── Calcular estadísticas y adjuntarlas a la respuesta ──
        result["player_stats"] = extract_player_stats(timeline)

        # ── Extraer user_id del JWT si viene en el header ──
        user_id: Optional[int] = None
        if credentials:
            payload = decode_access_token(credentials.credentials)
            if payload:
                try:
                    user_id = int(payload["sub"])
                except (KeyError, ValueError, TypeError):
                    pass

        # ── Auto-guardar en BD si los IDs son enteros válidos ──
        match_id = None
        try:
            p1_db_id = int(request.player1.id)
            p2_db_id = int(request.player2.id)
            match_id = _try_save_match(result, p1_db_id, p2_db_id, request.config, db, user_id)
        except (ValueError, TypeError):
            # IDs no numéricos (ej. "P1"/"P2" de demos) → no guardar
            pass

        if match_id is not None:
            result["match_db_id"] = match_id

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la simulación: {e}")
