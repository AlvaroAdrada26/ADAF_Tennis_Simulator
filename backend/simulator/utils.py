# backend/simulator/utils.py
import random
import numpy as np

def clip(x: float, lo: float, hi: float) -> float:
    """Limita el valor x al rango [lo, hi]."""
    return max(lo, min(hi, x))

def rand() -> float:
    """Devuelve un float aleatorio en [0, 1)."""
    return random.random()

def seed_all(seed: int | None) -> None:
    """Inicializa las semillas de random y numpy."""
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

# Constantes globales para identificar roles
SACADOR = "SACADOR"
RESTADOR = "RESTADOR"
RALLY_S = "RALLY_S"
RALLY_R = "RALLY_R"
