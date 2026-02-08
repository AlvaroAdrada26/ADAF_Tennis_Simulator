from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.simulator.api import run_match


router = APIRouter()


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


class MatchRequest(BaseModel):
    player1: PlayerData
    player2: PlayerData
    config: Optional[ConfigData] = None


# ------------------------------------------------------------
# Endpoints API
# ------------------------------------------------------------
@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.post("/simulate_match")
def simulate_match(request: MatchRequest) -> Dict[str, Any]:
    """
    Ejecuta una simulación de partido completa y devuelve el resultado detallado
    en formato JSON, incluyendo timeline punto a punto.
    """
    try:
        result = run_match(
            player1_data=request.player1.model_dump(),
            player2_data=request.player2.model_dump(),
            config=request.config.model_dump() if request.config else {},
        )

        timeline = result.get("timeline", [])
        for i, point in enumerate(timeline):
            point["point_index"] = i

        result["timeline"] = timeline
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la simulación: {e}")
