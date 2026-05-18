# backend/simulator/scoring.py
"""
Módulo de puntuación y flujo de partido (scoring) del ADAF Tennis Simulator.

Define las clases:
  - MatchStats: almacena y agrega estadísticas de todos los puntos del partido.
  - MatchSimulator: ejecuta un número determinado de puntos aislados (modo test).
  - TennisGame: simula un juego (game) con el sistema 0-15-30-40-Ad.
  - TennisSet: simula un set completo, con o sin tiebreak.
  - TennisMatch: simula un partido completo al mejor de 3 o 5 sets.

Este módulo está libre de prints/interacción, listo para uso desde FastAPI.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any

from .models import Player, PointResult, MatchStats
from .point import PointSimulator
from .utils import SACADOR, RESTADOR


# ============================================================
# Clase MatchSimulator (modo puntos sueltos)
# ============================================================

class MatchSimulator:
    """
    Simulador de puntos independientes (modo test/entrenamiento).
    No usa marcador, solo genera estadísticas globales de un número n de puntos.
    """

    def __init__(self, server: Player, returner: Player):
        self.server = server
        self.returner = returner

    def simulate_points(self, n: int, verbose: bool = False) -> MatchStats:
        stats = MatchStats()
        for _ in range(n):
            ps = PointSimulator(self.server, self.returner)
            res = ps.simulate(verbose=verbose)
            stats.add_point(res)
        return stats


# ============================================================
# Clase TennisGame (un juego)
# ============================================================

class TennisGame:
    """Simula un juego (game) con la secuencia de puntos 0–15–30–40–Ad."""

    point_names = ["0", "15", "30", "40", "Ad"]

    def __init__(self, server: Player, returner: Player,
                 p1: Player, p2: Player, game_no: int = 1):
        self.server = server
        self.returner = returner
        self.p1 = p1
        self.p2 = p2
        self.game_no = game_no
        self.points = {SACADOR: 0, RESTADOR: 0}
        self.feed: List[PointResult] = []
        self.point_counter = 0  # numerador de puntos dentro del juego
        self.isFinished = False


    def is_clutch_point(self) -> bool:
        """
        Determina si el punto actual es de presión (break point, deuce o ventaja).
        """
        s, r = self.points[SACADOR], self.points[RESTADOR]

        # Deuce o ventaja (puntos a 40 iguales)
        if s >= 3 and r >= 3:
            return True

        # Punto de break: restador a un punto de ganar el juego
        if s <= 3 and r == 3:
            return True

        return False

    def get_point_label(self, player: Player) -> str:
        """Devuelve '0','15','30','40','Ad' según la situación real del juego."""
        s, r = self.points[SACADOR], self.points[RESTADOR]
        if self.isFinished:
            return "0"
        if s < 3 and r < 3:
            return self.point_names[self.points[SACADOR if player == self.server else RESTADOR]]
        if s >= 3 and r >= 3:
            if self.isFinished:
                return "0"
            elif s == r:
                return "40"
            elif s == r + 1:
                return "Ad" if player == self.server else "40"
            elif r == s + 1:
                return "Ad" if player == self.returner else "40"
            else:
                return "40"
        return self.point_names[min(self.points[SACADOR if player == self.server else RESTADOR], 4)]

    def is_finished(self) -> Optional[str]:
        """Devuelve 'SACADOR' o 'RESTADOR' si el juego ha terminado."""
        s, r = self.points[SACADOR], self.points[RESTADOR]
        if s >= 4 and s >= r + 2:
            self.isFinished = True
            self.points[SACADOR] = 0
            self.points[RESTADOR] = 0
            return SACADOR
        if r >= 4 and r >= s + 2:
            self.isFinished = True
            self.points[RESTADOR] = 0
            self.points[SACADOR] = 0
            return RESTADOR
        return None

    def play(self, verbose: bool = False) -> str:
        """Juega un juego completo y devuelve el ganador ('SACADOR' o 'RESTADOR')."""
        while True:
            clutch = self.is_clutch_point()
            # Break point: restador a un punto de ganar el juego (antes del punto)
            s, r = self.points[SACADOR], self.points[RESTADOR]
            is_bp = r >= 3 and r > s  # cubre 40-0, 40-15, 40-30 y ventaja restador
            ps = PointSimulator(self.server, self.returner, clutch=clutch)

            res = ps.simulate(verbose=verbose)
            res.is_break_point = is_bp
            self.points[res.winner] += 1
            self.point_counter += 1
            res.point_no = self.point_counter
            res.game_no = self.game_no

            # Actualizar estamina de ambos jugadores
            for jugador in [self.server, self.returner]:
                # Fatiga proporcional a la duracion del punto e inversa al fisico
                fatiga = (0.5 + res.stats["rally_shots"] * 0.2) * (1.5 - jugador.Fisico / 100)
                jugador.Estamina = max(0.0, jugador.Estamina - fatiga)

            # === Actualizar momentum segun el resultado del punto ===
            if res.winner == SACADOR:
                ganador, perdedor = self.server, self.returner
            else:
                ganador, perdedor = self.returner, self.server

            # Actualizar momentum y racha
            ganador.streak = max(1, ganador.streak + 1)
            perdedor.streak = min(-1, perdedor.streak - 1)
            ganador.Momentum = min(50.0, ganador.Momentum + 2 * abs(ganador.streak))
            perdedor.Momentum = max(-50.0, perdedor.Momentum - 2 * abs(perdedor.streak))
            ganador.Momentum *= 0.97
            perdedor.Momentum *= 0.97

            # === Snapshot de momentum para exportacion ===
            res.momentum_p1 = self.p1.Momentum
            res.momentum_p2 = self.p2.Momentum

            winner = self.is_finished()

            score_label_server = self.get_point_label(self.server)
            score_label_returner = self.get_point_label(self.returner)
            res.score_after = {
                "server_points": score_label_server,
                "returner_points": score_label_returner,
                "game_progress": self.points.copy(),
            }

            self.feed.append(res)

            if winner:
                # Actualizar estamina de ambos jugadores
                for jugador in [self.p1, self.p2]:
                    rec = 0.3 + 0.8 * (jugador.Fisico / 100)
                    jugador.Estamina = min(100.0, jugador.Estamina + rec)

                # Bonus de momentum por ganar/perder juego
                for jugador in [self.p1, self.p2]:
                    if jugador == self.server and winner == SACADOR or jugador == self.returner and winner == RESTADOR:
                        jugador.Momentum = min(50.0, jugador.Momentum + 8.0)
                    else:
                        jugador.Momentum = max(-50.0, jugador.Momentum - 8.0)

                return winner


# ============================================================
# Clase TieBreakGame
# ============================================================

class TieBreakGame:
    """
    Simula un tie-break real (7 puntos con diferencia de 2).
    Cada punto se juega con PointSimulator.
    """

    def __init__(self, player1: Player, player2: Player, target_points: int = 7, set_no: int = 1, game_no: int = 13):
        self.p1 = player1
        self.p2 = player2
        self.target_points = target_points
        self.set_no = set_no
        self.game_no = game_no
        self.points = {"P1": 0, "P2": 0}
        self.server_flag = 0  # alternancia de servicio
        self.feed: List[PointResult] = []
        self.point_counter = 0

    # ------------------------------------------------------------
    def is_finished(self) -> Optional[str]:
        """Comprueba si el tie-break ha finalizado."""
        a, b = self.points["P1"], self.points["P2"]
        if (a >= self.target_points or b >= self.target_points) and abs(a - b) >= 2:
            return "P1" if a > b else "P2"
        return None

    # ------------------------------------------------------------
    def play(self, verbose: bool = False) -> Tuple[str, List[PointResult]]:
        """Juega el tie-break completo y devuelve (ganador, lista de puntos)."""
        while True:
            # Alternar saque cada 2 puntos tras el primero (regla oficial)
            if self.server_flag == 0:
                server, returner = self.p1, self.p2
            elif (self.server_flag - 1) % 4 < 2:
                server, returner = self.p2, self.p1
            else:
                server, returner = self.p1, self.p2

            ps = PointSimulator(server, returner, clutch=True)
            res = ps.simulate(verbose=verbose)

            # Determinar ganador (P1 / P2)
            winner_tag = (
                "P1" if (res.winner == SACADOR and server == self.p1) or (res.winner == RESTADOR and returner == self.p1)
                else "P2"
            )
            self.points[winner_tag] += 1
            self.point_counter += 1

            # Metadatos
            res.set_no = self.set_no
            res.game_no = self.game_no
            res.point_no = self.point_counter
            res.winner_id = winner_tag
            res.score_after = {
                "tiebreak_score": {"P1": self.points["P1"], "P2": self.points["P2"]},
                "server": "P1" if server == self.p1 else "P2",
            }

            # === Snapshot de momentum para exportacion ===
            res.momentum_p1 = self.p1.Momentum
            res.momentum_p2 = self.p2.Momentum

            self.feed.append(res)

            if verbose:
                print(f"Tie-break → {self.p1.name}: {self.points['P1']}, {self.p2.name}: {self.points['P2']}")

            self.server_flag += 1
            fin = self.is_finished()
            if fin:
                if verbose:
                    print(f"\n>>> TIE-BREAK ganado por {'Jugador 1' if fin == 'P1' else 'Jugador 2'} "
                          f"({self.points['P1']}–{self.points['P2']}) <<<")
                return fin, self.feed


# ============================================================
# Clase TennisSet
# ============================================================

class TennisSet:
    """Simula un set completo (con o sin tiebreak)."""

    def __init__(self, player1: Player, player2: Player,
                 tiebreak: bool = True, set_no: int = 1):
        self.p1 = player1
        self.p2 = player2
        self.tiebreak = tiebreak
        self.set_no = set_no
        self.games = {"P1": 0, "P2": 0}
        self.server_flag = 0  # alterna el sacador
        self.points_timeline: List[PointResult] = []  # todos los puntos del set

    # ------------------------------------------------------------
    def is_finished(self) -> Optional[str]:
        """Comprueba si el set ha finalizado (6–4, 7–5 o tie-break ganado)."""
        g1, g2 = self.games["P1"], self.games["P2"]
        if self.tiebreak:
            # Con tiebreak a 6–6
            if (g1 >= 6 or g2 >= 6) and abs(g1 - g2) >= 2:
                return "P1" if g1 > g2 else "P2"
            if (g1, g2) in [(7, 6), (6, 7)]:
                return "P1" if g1 > g2 else "P2"
        else:
            if g1 >= 6 and g1 >= g2 + 2:
                return "P1"
            if g2 >= 6 and g2 >= g1 + 2:
                return "P2"
        return None

    # ------------------------------------------------------------
    def _is_decisive_set(self) -> bool:
        """Devuelve True si este set es el último del partido (para tie-break a 10)."""
        # Este metodo podria recibir info desde TennisMatch si se quiere adaptar.
        return False

    # ------------------------------------------------------------
    def play(self, verbose: bool = False) -> Tuple[str, Tuple[int, int], List["PointResult"]]:
        """Simula un set completo y devuelve ('P1'/'P2', (juegos1, juegos2))."""
        game_no = 1
        while True:
            # Alternancia de servicio
            server, returner = (self.p1, self.p2) if self.server_flag % 2 == 0 else (self.p2, self.p1)
            tag_server, tag_returner = ("P1", "P2") if self.server_flag % 2 == 0 else ("P2", "P1")

            # === Juego normal ===
            game = TennisGame(server, returner, self.p1, self.p2, game_no=game_no)
            winner = game.play(verbose=verbose)

            # Anadir puntos de este juego al timeline
            for i, p in enumerate(game.feed[:-1]):
                p.set_no = self.set_no
                p.game_no = game_no

                # Determinar ganador por ID (P1 / P2)
                p.winner_id = "P1" if (
                    (p.winner == SACADOR and server == self.p1)
                    or (p.winner == RESTADOR and returner == self.p1)
                ) else "P2"

                # Nuevo: quien saca este punto
                p.server_id = "P1" if server == self.p1 else "P2"

                # Nuevo: este punto no es de tie-break
                p.is_tiebreak = False

                # Nuevo: marcar si es el ultimo punto del juego
                p.game_end = False

                # (set_end se marca mas adelante, al final del set)
                p.set_end = False

                # Marcador de juegos tras el punto
                if not hasattr(p, "score_after") or p.score_after is None:
                    p.score_after = {}
                p.score_after["set_games"] = self.games.copy()

                # Anadir al timeline del set
                self.points_timeline.append(p)

            # Ultimo punto del juego
            last_point = game.feed[-1]
            last_point.set_no = self.set_no
            last_point.game_no = game_no

            # Determinar ganador por ID (P1 / P2)
            last_point.winner_id = "P1" if (
                (last_point.winner == SACADOR and server == self.p1)
                or (last_point.winner == RESTADOR and returner == self.p1)
            ) else "P2"

            # Nuevo: quien saca este punto
            last_point.server_id = "P1" if server == self.p1 else "P2"

            # Nuevo: este punto no es de tie-break
            last_point.is_tiebreak = False

            # Nuevo: marcar si es el ultimo punto del juego
            last_point.game_end = True

            # (set_end se marca mas adelante, al final del set)
            last_point.set_end = False

            # Marcador de juegos tras el punto
            if not hasattr(last_point, "score_after") or last_point.score_after is None:
                last_point.score_after = {}
            
            score_after_aux = last_point.score_after.copy()
            if "set_games" not in score_after_aux:
                score_after_aux["set_games"] = self.games.copy()

            # Actualizar juegos ganados
            if winner == SACADOR:
                score_after_aux["set_games"][tag_server] += 1
                self.games[tag_server] += 1

            else:
                score_after_aux["set_games"][tag_returner] += 1
                self.games[tag_returner] += 1
            # Anadir al timeline del set

            last_point.score_after = score_after_aux.copy()
            self.points_timeline.append(last_point)

            # --- Comprobacion: Tie-break a 6–6 ---
            if self.tiebreak and self.games["P1"] == 6 and self.games["P2"] == 6:
                if verbose:
                    print("\n=== TIE-BREAK ===")
                tb_target = 10 if self._is_decisive_set() else 7
                tb = TieBreakGame(self.p1, self.p2, target_points=tb_target,
                                  set_no=self.set_no, game_no=game_no + 1)
                tb_winner, tb_points = tb.play(verbose=verbose)

                # Anadir puntos del tie-break al timeline del set
                for i, p in enumerate(tb_points):
                    p.set_no = self.set_no
                    p.winner_id = p.winner_id or ("P1" if p.winner == SACADOR and tb.p1 == self.p1 else "P2")
                    p.is_tiebreak = True
                    if p.score_after:
                        p.server_id = p.score_after.get("server")
                    if not hasattr(p, "score_after") or p.score_after is None:
                        p.score_after = {}
                    p.score_after["set_games"] = self.games.copy()
                    if i == len(tb_points) - 1:
                        p.game_end = True
                        p.set_end = True
                    self.points_timeline.append(p)

                # Actualizar el resultado del set tras el tie-break
                if tb_winner == "P1":
                    self.games["P1"] += 1
                else:
                    self.games["P2"] += 1

                # Recuperacion larga tras set (post tie-break)
                for jugador in [self.p1, self.p2]:
                    rec_set = 2 + 5 * (jugador.Fisico / 100)
                    jugador.Estamina = min(100.0, jugador.Estamina + rec_set)

                return tb_winner, (self.games["P1"], self.games["P2"]), self.points_timeline

            # --- Fin de juego ---
            self.server_flag += 1
            game_no += 1

            fin = self.is_finished()
            if fin:
                # Marcar ultimo punto como fin de set
                if self.points_timeline:
                    self.points_timeline[-1].set_end = True

                # Recuperacion tras set normal
                for jugador in [self.p1, self.p2]:
                    rec_set = 2 + 5 * (jugador.Fisico / 100)
                    jugador.Estamina = min(100.0, jugador.Estamina + rec_set)

                # Bonus adicional de momentum
                for jugador in [self.p1, self.p2]:
                    if (fin == "P1" and jugador == self.p1) or (fin == "P2" and jugador == self.p2):
                        jugador.Momentum = min(50.0, jugador.Momentum + 15.0)
                    else:
                        jugador.Momentum = max(-50.0, jugador.Momentum - 15.0)

                return fin, (self.games["P1"], self.games["P2"]), self.points_timeline


# ============================================================
# Clase TennisMatch
# ============================================================

class TennisMatch:
    """Simula un partido completo al mejor de N sets y genera JSON punto a punto."""
    def __init__(self, player1: Player, player2: Player, best_of: int = 3, tiebreak: bool = True):
        self.p1 = player1
        self.p2 = player2
        self.best_of = best_of
        self.tiebreak = tiebreak
        self.sets = {"P1": 0, "P2": 0}
        self.resultados_sets: List[Tuple[int, int]] = []
        self.timeline: List[PointResult] = []
        self.p1.reset_dynamic_state()
        self.p2.reset_dynamic_state()

    def is_finished(self) -> Optional[str]:
        needed = (self.best_of // 2) + 1
        if self.sets["P1"] >= needed:
            return "P1"
        if self.sets["P2"] >= needed:
            return "P2"
        return None

    def play(self, verbose: bool = False) -> Dict[str, Any]:
        """Juega el partido completo y devuelve un diccionario con el resultado y el timeline."""
        set_num = 1
        full_timeline: List[PointResult] = []

        while True:
            set_sim = TennisSet(self.p1, self.p2, tiebreak=self.tiebreak, set_no=set_num)
            ganador, marcador, set_timeline = set_sim.play(verbose=verbose)

            self.sets[ganador] += 1
            self.resultados_sets.append(marcador)
            full_timeline.extend(set_timeline)   # solo usamos el que devuelve el set

            fin = self.is_finished()
            if fin:
                winner_id = fin
                winner_name = self.p1.name if fin == "P1" else self.p2.name
                names = {"P1": self.p1.name, "P2": self.p2.name}

                return {
                    "players": {"P1": self.p1.name, "P2": self.p2.name},
                    "winner_id": winner_id,
                    "winner_name": winner_name,
                    "sets_won": self.sets,
                    "set_scores": self.resultados_sets,
                    "timeline": [p.to_dict(names) for p in full_timeline],
                    "best_of": self.best_of,
                    "tiebreak": self.tiebreak,
                }

            set_num += 1
