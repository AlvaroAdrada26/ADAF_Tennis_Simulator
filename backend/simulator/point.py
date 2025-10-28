# backend/simulator/point.py
"""
Simulador de punto (PointSimulator) del ADAF Tennis Simulator.

Coordina las tres fases del punto:
  1. Saque (Serve)
  2. Resto (ReturnShot)
  3. Peloteo (RallyShot)
Aplicando las fórmulas exactas de cada etapa y registrando estadísticas
intermedias (aces, dobles faltas, duración del rally, etc.).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from .models import Player, Ball, PointResult
from .shots import Serve, ReturnShot, RallyShot
from .utils import SACADOR, RESTADOR


class PointSimulator:
    def __init__(self, server: Player, returner: Player, clutch: bool = False, tags: Optional[Dict[str, str]] = None):
        self.S = server
        self.R = returner
        self.clutch = clutch
        self.tags = tags or {"SACADOR": "P1", "RESTADOR": "P2"}
        self.actions: List[Dict] = []


    def simulate(self, verbose: bool = True) -> PointResult:
        feed: List[str] = []
        stats = {
            "aces": 0,
            "double_faults": 0,
            "first_in": 0,
            "first_total": 0,
            "second_in": 0,
            "second_total": 0,
            "rally_shots": 0,
        }

        def translate_winner(winner_tag: str) -> str:  # 👈 nuevo
            return self.tags.get(winner_tag, "NINGUNO")

        # ============================================================
        # 1️⃣ SAQUE
        # ============================================================
        srv = Serve(self.S, self.R, feed, clutch=self.clutch)
        ball, slog = srv.serve_sequence()

        isFirst = True
        stats["first_total"] += 1
        if slog["first"]["in"]:
            stats["first_in"] += 1
        if slog["second"] is not None:
            stats["second_total"] += 1
            isFirst = False
            if slog["second"]["in"]:
                stats["second_in"] += 1
        if slog["double_fault"]:
            stats["double_faults"] += 1
            feed.append(">>> Resultado: DOBLE FALTA")
            return PointResult(
                winner=RESTADOR,
                winner_id=translate_winner(RESTADOR),  # 👈 nuevo
                reason="doble_falta",
                feed=feed,
                stats=stats
            )

        # ============================================================
        # 2️⃣ RESTO
        # ============================================================
        ret = ReturnShot(self.S, self.R, feed, clutch=self.clutch)
        ok, pr_reach = ret.attempt_reach(ball, isFirst)
        if not ok:
            stats["aces"] += 1
            feed.append(">>> Resultado: ACE")
            return PointResult(
                winner=SACADOR,
                winner_id=translate_winner(SACADOR),  # 👈 nuevo
                reason="ace",
                feed=feed,
                stats=stats
            )

        ball, rlog = ret.produce_ball(ball)
        if ball is None:
            feed.append(">>> Resultado: ERROR DE RESTO")
            return PointResult(
                winner=SACADOR,
                winner_id=translate_winner(SACADOR),
                reason="error_resto",
                feed=feed,
                stats=stats
            )

        # ============================================================
        # 3️⃣ RALLY
        # ============================================================
        while True:
            stats["rally_shots"] += 1

            if ball.by in (SACADOR, "RALLY_S"):
                hitter_obj, other_obj, tag_prev = self.R, self.S, SACADOR
            else:
                hitter_obj, other_obj, tag_prev = self.S, self.R, RESTADOR

            rally = RallyShot(hitter_obj, other_obj, feed, clutch=self.clutch)
            ok, pr = rally.attempt_reach(ball)
            if not ok:
                feed.append(f">>> Resultado: PUNTO para {tag_prev} (no llega)")
                return PointResult(
                    winner=tag_prev,
                    winner_id=translate_winner(tag_prev),  # 👈 nuevo
                    reason="no_llega",
                    feed=feed,
                    stats=stats
                )

            ball2, log = rally.produce_ball(ball)
            if ball2 is None:
                feed.append(f">>> Resultado: PUNTO para {tag_prev} (falla golpe)")
                return PointResult(
                    winner=tag_prev,
                    winner_id=translate_winner(tag_prev), 
                    reason="error_golpe",
                    feed=feed,
                    stats=stats
                )

            ball = ball2
            ball.by = "RALLY_R" if tag_prev == SACADOR else "RALLY_S"
