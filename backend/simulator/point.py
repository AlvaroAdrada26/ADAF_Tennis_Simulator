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

from .models import Player, Ball, PointResult, Action
from .shots import Serve, ReturnShot, RallyShot
from .utils import SACADOR, RESTADOR


class PointSimulator:
    def __init__(self, server: Player, returner: Player, clutch: bool = False,
                 tags: Optional[Dict[str, str]] = None,
                 server_strategy: Optional[Dict[str, float]] = None,
                 returner_strategy: Optional[Dict[str, float]] = None):
        self.S = server
        self.R = returner
        self.clutch = clutch
        self.tags = tags or {"SACADOR": "P1", "RESTADOR": "P2"}
        self.actions: List[Dict] = []
        self.server_strategy = server_strategy
        self.returner_strategy = returner_strategy


    def simulate(self, verbose: bool = True) -> PointResult:
        feed: List[str] = []
        actions: List[Action] = []
        stats = {
            "aces": 0,
            "double_faults": 0,
            "first_in": 0,
            "first_total": 0,
            "second_in": 0,
            "second_total": 0,
            "rally_shots": 0,
        }

        def translate_winner(winner_tag: str) -> str:
            return self.tags.get(winner_tag, "NINGUNO")

        # ============================================================
        # SAQUE
        # ============================================================
        srv = Serve(self.S, self.R, feed, clutch=self.clutch, strategy=self.server_strategy)
        ball, slog = srv.serve_sequence()

        # Registrar primer saque
        actions.append(Action(
            action_index=len(actions),
            actor_id=self.S.id,
            action_type="FIRST_SERVE",
            outcome="IN" if slog["first"]["in"] else "FAULT",
            power=slog["first"]["pot"],
            precision=slog["first"]["prec"],
            clutch=self.clutch
        ))

        # --- Segundo saque (si hubo) ---
        if slog["second"] is not None:
            actions.append(Action(
                action_index=len(actions),
                actor_id=self.S.id,
                action_type="SECOND_SERVE",
                outcome="IN" if slog["second"]["in"] else "DOBLE_FAULT",
                power=slog["second"]["pot"],
                precision=slog["second"]["prec"],
                clutch=self.clutch
            ))

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
                winner_id=translate_winner(RESTADOR),
                reason="doble_falta",
                feed=feed,
                stats=stats,
                actions=actions
            )

        # ============================================================
        # RESTO
        # ============================================================
        ret = ReturnShot(self.S, self.R, feed, clutch=self.clutch, strategy=self.returner_strategy)
        ok, pr_reach = ret.attempt_reach(ball, isFirst)

        # --- Intento de alcanzar saque ---
        actions.append(Action(
            action_index=len(actions),
            actor_id=self.R.id,
            action_type="REACH",
            outcome="REACHED" if ok else "NOT_REACHED",
            clutch=self.clutch
        ))

        if not ok:
            stats["aces"] += 1
            feed.append(">>> Resultado: ACE")
            return PointResult(
                winner=SACADOR,
                winner_id=translate_winner(SACADOR),
                reason="ace",
                feed=feed,
                stats=stats,
                actions=actions
            )

        ball, rlog = ret.produce_ball(ball)
        # --- Golpe de resto ---
        actions.append(Action(
            action_index=len(actions),
            actor_id=self.R.id,
            action_type="RETURN",
            outcome="IN" if rlog["in"] else "OUT",
            shot_type=rlog["side"],
            power=rlog["pot"],
            precision=rlog["prec"],
            clutch=self.clutch
        ))

        if ball is None:
            feed.append(">>> Resultado: ERROR DE RESTO")
            return PointResult(
                winner=SACADOR,
                winner_id=translate_winner(SACADOR),
                reason="error_resto",
                feed=feed,
                stats=stats,
                actions=actions
            )

        # ============================================================
        # RALLY
        # ============================================================
        while True:
            stats["rally_shots"] += 1

            if ball.by in (SACADOR, "RALLY_S"):
                hitter_obj, other_obj, tag_prev = self.R, self.S, SACADOR
                hitter_strategy = self.returner_strategy
            else:
                hitter_obj, other_obj, tag_prev = self.S, self.R, RESTADOR
                hitter_strategy = self.server_strategy

            rally = RallyShot(hitter_obj, other_obj, feed, clutch=self.clutch, strategy=hitter_strategy)
            ok, pr = rally.attempt_reach(ball)

            # --- Intento de alcanzar durante rally ---
            actions.append(Action(
                action_index=len(actions),
                actor_id=hitter_obj.id,
                action_type="REACH",
                outcome="REACHED" if ok else "NOT_REACHED",
                clutch=self.clutch
            ))

            if not ok:
                feed.append(f">>> Resultado: PUNTO para {tag_prev} (no llega)")
                return PointResult(
                    winner=tag_prev,
                    winner_id=translate_winner(tag_prev),
                    reason="no_llega",
                    feed=feed,
                    stats=stats,
                    actions=actions
                )

            ball2, log = rally.produce_ball(ball)

            # --- Golpe durante rally ---
            actions.append(Action(
                action_index=len(actions),
                actor_id=hitter_obj.id,
                action_type="RALLY_SHOT",
                outcome="IN" if log["in"] else "OUT",
                shot_type=log["side"],
                power=log["pot"],
                precision=log["prec"],
                clutch=self.clutch
            ))

            if ball2 is None:
                feed.append(f">>> Resultado: PUNTO para {tag_prev} (falla golpe)")
                return PointResult(
                    winner=tag_prev,
                    winner_id=translate_winner(tag_prev), 
                    reason="error_golpe",
                    feed=feed,
                    stats=stats,
                    actions=actions
                )

            ball = ball2
            ball.by = "RALLY_R" if tag_prev == SACADOR else "RALLY_S"
