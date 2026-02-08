# backend/app/main.py
"""
FastAPI backend para el ADAF Tennis Simulator.

Expone un endpoint principal /simulate_match que ejecuta una simulación completa
usando el motor Python del simulador (backend/simulator).
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

from backend.simulator.api import run_match


# ============================================================
# Definición de modelos de entrada (validados por Pydantic)
# ============================================================

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
    config: ConfigData | None = None


# ============================================================
# Inicialización de la aplicación
# ============================================================

app = FastAPI(
    title="ADAF Tennis Simulator API",
    description="API del simulador estadístico de tenis.",
    version="1.0.0",
)

# Permitir conexiones desde el frontend (localhost:5500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes limitar a ["http://127.0.0.1:5500"] para más seguridad
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Endpoints
# ============================================================

@app.get("/")
def root() -> Dict[str, str]:
    """Endpoint de prueba para verificar que el backend funciona."""
    return {"mensaje": "🎾 FastAPI + ADAF Simulator funcionando correctamente!"}


@app.post("/simulate_match")
def simulate_match(request: MatchRequest) -> Dict[str, Any]:
    """
    Ejecuta una simulación de partido completa y devuelve el resultado detallado
    en formato JSON, incluyendo timeline punto a punto.
    """
    try:
        # Ejecutar la simulación principal (devuelve JSON completo del partido)
        result = run_match(
            player1_data=request.player1.model_dump(),
            player2_data=request.player2.model_dump(),
            config=request.config.model_dump() if request.config else {},
        )
        timeline = result.get("timeline", [])
        for i, point in enumerate(timeline):
            point["point_index"] = i  # índice secuencial absoluto

        # Guardar el timeline actualizado
        result["timeline"] = timeline

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la simulación: {e}")
