# backend/simulator/models.py
"""Entidades principales (jugadores, bola, resultados, configuración) del simulador ADAF."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


import numpy as np
from .utils import SACADOR, RESTADOR

@dataclass(slots=True)
class Player:
    name: str
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

    # --- Estado interno dinámico (no recibido por API) ---
    streak: int = field(default=0, repr=False)

    # --- Propiedades normalizadas (0..1) ---
    @property
    def S1(self): return self.Primer_Saque / 100
    @property
    def S2(self): return self.Segundo_Saque / 100
    @property
    def F(self): return self.Fisico / 100
    @property
    def E(self): return self.Estamina / 100
    @property
    def C(self): return self.Consistencia / 100
    @property
    def K(self): return self.Clutch / 100
    @property
    def M(self): return self.Momentum / 100
    @property
    def FH(self): return self.Derecha / 100
    @property
    def BH(self): return self.Reves / 100
    @property
    def RET(self): return self.Resto / 100
    @property
    def MOV(self): return self.Movilidad / 100

    # --- Métodos auxiliares ---
    def pick_side(self) -> tuple[str, float]:
        """Elige entre derecha (FH) o revés (BH) con ligera aleatoriedad."""
        if np.random.rand() < self.FH / (self.FH + self.BH + 1e-9):
            return "FH", self.FH
        else:
            return "BH", self.BH

    def reset_dynamic_state(self):
        """
        Reinicia las variables dinámicas del jugador antes de cada partido.
        """
        self.Estamina = 100.0       # energía inicial completa
        self.Momentum = 0.0         # sin impulso inicial
        self.streak = 0             # sin racha activa

 


@dataclass(slots=True)
class Ball:
    pot: float
    prec: float
    side: str  # "S", "FH", "BH"
    by: str    # "SACADOR", "RESTADOR", "RALLY_S", "RALLY_R"

    @property
    def shotQ(self) -> float:
        from .utils import clip
        return clip(0.65 * self.pot + 0.35 * self.prec, 0.0, 1.0)


@dataclass(slots=True)
class PointResult:
    winner: str
    reason: str
    feed: List[str] = field(default_factory=list)
    stats: Dict = field(default_factory=dict)


@dataclass(slots=True)
class MatchStats:
    total_points: int = 0
    server_points_won: int = 0
    returner_points_won: int = 0
    first_in: int = 0
    first_total: int = 0
    second_in: int = 0
    second_total: int = 0
    aces: int = 0
    double_faults: int = 0
    rally_shots: List[int] = field(default_factory=list)
    reasons: Dict[str, int] = field(default_factory=dict)
    points_feed: List[PointResult] = field(default_factory=list)

    # ============================================================
    # Métodos de agregación y exportación
    # ============================================================

    def add_point(self, res: PointResult):
        """Incorpora los datos de un punto jugado a las estadísticas acumuladas."""
        self.total_points += 1
        if res.winner == SACADOR:
            self.server_points_won += 1
        elif res.winner == RESTADOR:
            self.returner_points_won += 1

        self.first_in += res.stats["first_in"]
        self.first_total += res.stats["first_total"]
        self.second_in += res.stats["second_in"]
        self.second_total += res.stats["second_total"]
        self.aces += res.stats["aces"]
        self.double_faults += res.stats["double_faults"]
        self.rally_shots.append(res.stats["rally_shots"])
        self.reasons[res.reason] = self.reasons.get(res.reason, 0) + 1
        self.points_feed.append(res)

    def to_dict(self, include_feed: bool = False) -> Dict:
        """Convierte las estadísticas a un diccionario serializable."""
        from numpy import mean  # evitar import global innecesario
        d = {
            "total_points": self.total_points,
            "server_points_won": self.server_points_won,
            "returner_points_won": self.returner_points_won,
            "first_in_pct": self._pct(self.first_in, self.first_total),
            "second_in_pct": self._pct(self.second_in, self.second_total),
            "aces": self.aces,
            "double_faults": self.double_faults,
            "avg_rally_len": float(mean(self.rally_shots)) if self.rally_shots else 0,
            "reasons": self.reasons,
        }
        if include_feed:
            d["points_feed"] = [vars(p) for p in self.points_feed]
        return d

    @staticmethod
    def _pct(a: int, b: int) -> float:
        return round(100 * a / b, 2) if b > 0 else 0.0



@dataclass(slots=True)
class Config:
    best_of: int = 3
    tiebreak: bool = True
    collect_feed: bool = False
    seed: Optional[int] = None
