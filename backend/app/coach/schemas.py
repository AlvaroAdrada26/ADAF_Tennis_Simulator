# backend/app/coach/schemas.py
"""Schemas Pydantic para los endpoints del Modo Entrenador."""

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


class CoachConfig(BaseModel):
    best_of: int = 3
    tiebreak: bool = True
    superficie: Optional[str] = None


class CoachStartRequest(BaseModel):
    player1: PlayerData
    player2: PlayerData
    coached_player: str = Field(pattern=r"^P[12]$")
    config: Optional[CoachConfig] = None


class CoachNextPointRequest(BaseModel):
    session_id: str
    strategy: Optional[str] = None  # "aggressive" | "neutral" | "defensive"


class CoachSetStrategyRequest(BaseModel):
    session_id: str
    strategy: str = Field(pattern=r"^(aggressive|neutral|defensive)$")


class CoachEndRequest(BaseModel):
    session_id: str


class CoachSaveRequest(BaseModel):
    session_id: str
