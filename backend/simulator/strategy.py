# backend/simulator/strategy.py
"""
Constantes de estrategia táctica para el Modo Estratégico.

Cada estrategia define multiplicadores que se aplican DESPUÉS de los cálculos
base de las fórmulas de golpes (Serve, ReturnShot, RallyShot).
Cuando strategy es None o "neutral", los multiplicadores son 1.0 (sin efecto).
"""

from __future__ import annotations
from typing import Dict

STRATEGY_MODIFIERS: Dict[str, Dict[str, float]] = {
    "aggressive": {
        "pot_mult": 1.12,          # +12% potencia en todos los golpes
        "prec_mult": 0.96,         # -4% precision
        "p_in_mult": 0.97,         # -3% probabilidad de meter la bola
        "reach_mult": 1.02,        # +2% alcance (juega mas adelantado)
        "sigma_pot_mult": 1.06,    # +6% varianza en potencia (mas irregular)
        "sigma_prec_mult": 1.08,   # +8% varianza en precision
    },
    "neutral": {
        "pot_mult": 1.00,
        "prec_mult": 1.00,
        "p_in_mult": 1.00,
        "reach_mult": 1.00,
        "sigma_pot_mult": 1.00,
        "sigma_prec_mult": 1.00,
    },
    "defensive": {
        "pot_mult": 0.92,          # -8% potencia
        "prec_mult": 1.02,         # +2% precision
        "p_in_mult": 1.015,        # +1.5% probabilidad de meter la bola
        "reach_mult": 1.03,        # +3% alcance (juega mas atras, llega a mas)
        "sigma_pot_mult": 0.94,    # -6% varianza (mas regular)
        "sigma_prec_mult": 0.93,   # -7% varianza (mas consistente)
    },
}

VALID_STRATEGIES = frozenset(STRATEGY_MODIFIERS.keys())


def get_modifiers(strategy: str | None) -> Dict[str, float] | None:
    """Devuelve los modificadores para una estrategia dada, o None si no aplica."""
    if strategy is None:
        return None
    return STRATEGY_MODIFIERS.get(strategy)
