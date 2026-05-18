# backend/simulator/api.py
"""
API pública del simulador ADAF Tennis Simulator.

Proporciona la función principal `run_match(player1_data, player2_data, config)`
que ejecuta un partido completo y devuelve el resultado estructurado,
listo para ser enviado como respuesta JSON desde FastAPI.
"""

from __future__ import annotations
import json
import sys
import traceback
from typing import Dict, Any
from .models import Player, Config
from .scoring import TennisMatch
from .utils import seed_all


def run_match(player1_data: Dict[str, Any],
              player2_data: Dict[str, Any],
              config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Ejecuta un partido completo entre dos jugadores.

    Parámetros
    ----------
    player1_data : dict
        Diccionario con los atributos del jugador 1 (coinciden con Player).
    player2_data : dict
        Diccionario con los atributos del jugador 2.
    config : dict, opcional
        Configuración general del partido:
          - best_of: int = 3
          - tiebreak: bool = True
          - seed: int | None = None

    Devuelve
    --------
    dict con:
        - "players": {"P1": nombre, "P2": nombre}
        - "winner_name": nombre del ganador
        - "winner_id": "P1" o "P2"
        - "sets_won": {"P1": int, "P2": int}
        - "set_scores": lista de tuplas [(6,4), (3,6), ...]
        - "best_of": int
        - "tiebreak": bool
        - "timeline": lista de puntos con estructura detallada
    """
    # --------------------------------------------------------
    # Inicializacion
    # --------------------------------------------------------
    cfg = Config(**(config or {}))
    seed_all(cfg.seed)

    p1 = Player(**player1_data)
    p2 = Player(**player2_data)

    # --------------------------------------------------------
    # Ejecucion del partido completo
    # --------------------------------------------------------
    match = TennisMatch(
        p1, p2,
        best_of=cfg.best_of,
        tiebreak=cfg.tiebreak
    )

    # TennisMatch.play() devuelve ya un dict estructurado
    result = match.play(verbose=False)

    # --------------------------------------------------------
    # Devolver resultado directamente
    # --------------------------------------------------------
    return result
