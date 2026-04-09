# backend/app/coach/models.py
"""Modelo de sesión del Modo Entrenador."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from backend.simulator.models import Player
from backend.simulator.scorekeeper import MatchScorekeeper


@dataclass
class CoachSession:
    session_id: str
    player1: Player
    player2: Player
    scorekeeper: MatchScorekeeper
    coached_player: str                      # "P1" | "P2"
    current_strategy: str = "neutral"        # "aggressive" | "neutral" | "defensive"
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    match_finished: bool = False
    winner: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
