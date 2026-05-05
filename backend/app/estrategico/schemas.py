# backend/app/estrategico/schemas.py
"""Schemas Pydantic para los endpoints del Modo Estratégico."""

from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple

from pydantic import BaseModel, Field


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


class EstrategicoConfig(BaseModel):
    best_of: int = 3
    tiebreak: bool = True
    superficie: Optional[str] = None


class EstrategicoStartRequest(BaseModel):
    player1: PlayerData
    player2: PlayerData
    coached_player: str = Field(pattern=r"^P[12]$")
    config: Optional[EstrategicoConfig] = None


class EstrategicoNextPointRequest(BaseModel):
    session_id: str
    strategy: Optional[str] = None  # "aggressive" | "neutral" | "defensive"


class EstrategicoSetStrategyRequest(BaseModel):
    session_id: str
    strategy: str = Field(pattern=r"^(aggressive|neutral|defensive)$")


class EstrategicoEndRequest(BaseModel):
    session_id: str


class EstrategicoSaveRequest(BaseModel):
    session_id: str
