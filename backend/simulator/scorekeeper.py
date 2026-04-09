# backend/simulator/scorekeeper.py
"""
MatchScorekeeper – gestión del marcador punto a punto para el Modo Entrenador.

Encapsula TODA la lógica de puntuación (puntos → juegos → sets → partido)
que en el modo normal está distribuida entre TennisGame, TennisSet y TennisMatch.
También replica las fórmulas de estamina y momentum exactamente.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any

from .models import Player
from .utils import SACADOR, RESTADOR


_POINT_NAMES = ["0", "15", "30", "40", "Ad"]


class MatchScorekeeper:
    """Gestiona el marcador de un partido punto a punto, sin simular."""

    def __init__(self, p1: Player, p2: Player, best_of: int = 3,
                 tiebreak: bool = True):
        self.p1 = p1
        self.p2 = p2
        self.best_of = best_of
        self.tiebreak_enabled = tiebreak
        self.sets_needed = (best_of // 2) + 1

        # marcador
        self.sets: Dict[str, int] = {"P1": 0, "P2": 0}
        self.set_scores: List[Tuple[int, int]] = []
        self.current_set = 1
        self.games: Dict[str, int] = {"P1": 0, "P2": 0}
        self.points: Dict[str, int] = {SACADOR: 0, RESTADOR: 0}

        # saque
        self.server_flag = 0  # 0 → P1 saca, 1 → P2 saca, etc.

        # tiebreak
        self.is_tiebreak = False
        self.tb_points: Dict[str, int] = {"P1": 0, "P2": 0}
        self.tb_server_flag = 0

        # estado general
        self.match_finished = False
        self.winner: Optional[str] = None
        self.game_no = 1
        self.point_no = 0

    # ── helpers de saque ──────────────────────────────────
    def get_server_returner(self) -> Tuple[str, str]:
        """Devuelve (server_id, returner_id) para el próximo punto."""
        if self.is_tiebreak:
            if self.tb_server_flag == 0:
                server = "P1" if self.server_flag % 2 == 0 else "P2"
            elif (self.tb_server_flag - 1) % 4 < 2:
                server = "P2" if self.server_flag % 2 == 0 else "P1"
            else:
                server = "P1" if self.server_flag % 2 == 0 else "P2"
            returner = "P2" if server == "P1" else "P1"
            return server, returner

        if self.server_flag % 2 == 0:
            return "P1", "P2"
        return "P2", "P1"

    def get_player(self, pid: str) -> Player:
        return self.p1 if pid == "P1" else self.p2

    # ── clutch ────────────────────────────────────────────
    def is_clutch_point(self) -> bool:
        if self.is_tiebreak:
            return True
        s, r = self.points[SACADOR], self.points[RESTADOR]
        if s >= 3 and r >= 3:
            return True
        if s <= 3 and r == 3:
            return True
        return False

    # ── break point ───────────────────────────────────────
    def is_break_point(self) -> bool:
        if self.is_tiebreak:
            return False
        s, r = self.points[SACADOR], self.points[RESTADOR]
        return r >= 3 and r > s

    # ── etiqueta de puntos ────────────────────────────────
    def get_point_labels(self) -> Dict[str, str]:
        if self.is_tiebreak:
            return {
                "P1": str(self.tb_points["P1"]),
                "P2": str(self.tb_points["P2"]),
            }
        s, r = self.points[SACADOR], self.points[RESTADOR]
        server_id, returner_id = self.get_server_returner()
        if s < 3 or r < 3:
            sl = _POINT_NAMES[s] if s <= 4 else "40"
            rl = _POINT_NAMES[r] if r <= 4 else "40"
        else:
            if s == r:
                sl = rl = "40"
            elif s == r + 1:
                sl, rl = "Ad", "40"
            elif r == s + 1:
                sl, rl = "40", "Ad"
            else:
                sl = rl = "40"
        return {server_id: sl, returner_id: rl}

    # ── registro de punto ─────────────────────────────────
    def register_point(self, winner_tag: str, rally_shots: int) -> Dict[str, Any]:
        """
        Registra un punto ganado y actualiza el marcador.

        Parámetros
        ----------
        winner_tag : str
            "SACADOR" o "RESTADOR" — quién gana el punto.
        rally_shots : int
            Número de golpes de rally (para calcular fatiga).

        Devuelve
        --------
        dict con las transiciones ocurridas.
        """
        self.point_no += 1
        server_id, returner_id = self.get_server_returner()
        winner_id = server_id if winner_tag == SACADOR else returner_id
        loser_id = "P2" if winner_id == "P1" else "P1"

        events: Dict[str, Any] = {
            "game_end": False,
            "set_end": False,
            "match_end": False,
            "winner_id": winner_id,
            "server_id": server_id,
        }

        # ── Fatiga por punto ──
        for pid in ("P1", "P2"):
            p = self.get_player(pid)
            fatiga = (0.5 + rally_shots * 0.2) * (1.5 - p.Fisico / 100)
            p.Estamina = max(0.0, p.Estamina - fatiga)

        # ── Momentum por punto ──
        g = self.get_player(winner_id)
        l = self.get_player(loser_id)
        g.streak = max(1, g.streak + 1)
        l.streak = min(-1, l.streak - 1)
        g.Momentum = min(50.0, g.Momentum + 2 * abs(g.streak))
        l.Momentum = max(-50.0, l.Momentum - 2 * abs(l.streak))
        g.Momentum *= 0.97
        l.Momentum *= 0.97

        if self.is_tiebreak:
            self._register_tiebreak_point(winner_id, events)
        else:
            self._register_game_point(winner_tag, events)

        return events

    # ── juego normal ──────────────────────────────────────
    def _register_game_point(self, winner_tag: str, events: dict):
        self.points[winner_tag] += 1
        s, r = self.points[SACADOR], self.points[RESTADOR]

        # ¿Game terminado?
        game_winner_tag: Optional[str] = None
        if s >= 4 and s >= r + 2:
            game_winner_tag = SACADOR
        elif r >= 4 and r >= s + 2:
            game_winner_tag = RESTADOR

        if game_winner_tag is None:
            return

        # Game terminado
        events["game_end"] = True
        self.points[SACADOR] = 0
        self.points[RESTADOR] = 0

        server_id, returner_id = self.get_server_returner()
        game_winner_id = server_id if game_winner_tag == SACADOR else returner_id

        self.games[game_winner_id] += 1

        # Recuperación de estamina tras juego
        for pid in ("P1", "P2"):
            p = self.get_player(pid)
            rec = 0.3 + 0.8 * (p.Fisico / 100)
            p.Estamina = min(100.0, p.Estamina + rec)

        # Bonus momentum por game
        for pid in ("P1", "P2"):
            p = self.get_player(pid)
            if pid == game_winner_id:
                p.Momentum = min(50.0, p.Momentum + 8.0)
            else:
                p.Momentum = max(-50.0, p.Momentum - 8.0)

        # ¿Entrar en tiebreak? (6-6)
        if (self.tiebreak_enabled
                and self.games["P1"] == 6 and self.games["P2"] == 6):
            self.is_tiebreak = True
            self.tb_points = {"P1": 0, "P2": 0}
            self.tb_server_flag = 0
            self.server_flag += 1
            self.game_no += 1
            return

        # ¿Set terminado?
        self._check_set_end(events)

        if not events["set_end"]:
            self.server_flag += 1
            self.game_no += 1

    # ── tiebreak ──────────────────────────────────────────
    def _register_tiebreak_point(self, winner_id: str, events: dict):
        self.tb_points[winner_id] += 1
        self.tb_server_flag += 1

        a, b = self.tb_points["P1"], self.tb_points["P2"]
        target = 7
        if (a >= target or b >= target) and abs(a - b) >= 2:
            tb_winner = "P1" if a > b else "P2"
            events["game_end"] = True
            events["set_end"] = True

            self.games[tb_winner] += 1
            self.set_scores.append((self.games["P1"], self.games["P2"]))
            self.sets[tb_winner] += 1

            # Recuperación tras set (incluido tiebreak)
            for pid in ("P1", "P2"):
                p = self.get_player(pid)
                rec_set = 2 + 5 * (p.Fisico / 100)
                p.Estamina = min(100.0, p.Estamina + rec_set)

            # Bonus momentum por set
            for pid in ("P1", "P2"):
                p = self.get_player(pid)
                if pid == tb_winner:
                    p.Momentum = min(50.0, p.Momentum + 15.0)
                else:
                    p.Momentum = max(-50.0, p.Momentum - 15.0)

            self._check_match_end(events)
            if not events["match_end"]:
                self._start_new_set()

    # ── comprobaciones de set / match ─────────────────────
    def _check_set_end(self, events: dict):
        g1, g2 = self.games["P1"], self.games["P2"]
        set_winner: Optional[str] = None

        if self.tiebreak_enabled:
            if (g1 >= 6 or g2 >= 6) and abs(g1 - g2) >= 2:
                set_winner = "P1" if g1 > g2 else "P2"
        else:
            if g1 >= 6 and g1 >= g2 + 2:
                set_winner = "P1"
            elif g2 >= 6 and g2 >= g1 + 2:
                set_winner = "P2"

        if set_winner is None:
            return

        events["set_end"] = True
        self.set_scores.append((self.games["P1"], self.games["P2"]))
        self.sets[set_winner] += 1

        # Recuperación tras set
        for pid in ("P1", "P2"):
            p = self.get_player(pid)
            rec_set = 2 + 5 * (p.Fisico / 100)
            p.Estamina = min(100.0, p.Estamina + rec_set)

        # Bonus momentum por set
        for pid in ("P1", "P2"):
            p = self.get_player(pid)
            if pid == set_winner:
                p.Momentum = min(50.0, p.Momentum + 15.0)
            else:
                p.Momentum = max(-50.0, p.Momentum - 15.0)

        self._check_match_end(events)
        if not events["match_end"]:
            self._start_new_set()

    def _check_match_end(self, events: dict):
        if self.sets["P1"] >= self.sets_needed:
            self.match_finished = True
            self.winner = "P1"
            events["match_end"] = True
        elif self.sets["P2"] >= self.sets_needed:
            self.match_finished = True
            self.winner = "P2"
            events["match_end"] = True

    def _start_new_set(self):
        self.current_set += 1
        self.games = {"P1": 0, "P2": 0}
        self.points = {SACADOR: 0, RESTADOR: 0}
        self.is_tiebreak = False
        self.tb_points = {"P1": 0, "P2": 0}
        self.tb_server_flag = 0
        self.server_flag += 1
        self.game_no = 1

    # ── snapshot ──────────────────────────────────────────
    def get_score_snapshot(self) -> Dict[str, Any]:
        server_id, returner_id = self.get_server_returner()
        point_labels = self.get_point_labels()
        return {
            "sets": dict(self.sets),
            "set_scores": list(self.set_scores),
            "games": dict(self.games),
            "points": point_labels,
            "server_id": server_id,
            "current_set": self.current_set,
            "is_tiebreak": self.is_tiebreak,
            "match_finished": self.match_finished,
            "winner": self.winner,
        }
