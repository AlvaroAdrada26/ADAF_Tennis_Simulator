# backend/simulator/__init__.py
"""
ADAF Tennis Simulator - core simulation package.

Este módulo agrupa el motor de simulación del TFG.
Incluye las entidades principales (Player, Config, etc.) y
la función pública `run_match` para ejecutar un partido completo.
"""

from .api import run_match
from .models import Player, Config, MatchStats
from .utils import SACADOR, RESTADOR
from .shots import Serve, ReturnShot, RallyShot

__all__ = [
    "run_match",
    "Player",
    "Config",
    "MatchStats",
    "SACADOR",
    "RESTADOR",
]
