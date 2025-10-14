# backend/simulator/scoring.py
"""
Módulo de puntuación y flujo de partido (scoring) del ADAF Tennis Simulator.

Define las clases:
  - MatchStats: almacena y agrega estadísticas de todos los puntos del partido.
  - MatchSimulator: ejecuta un número determinado de puntos aislados (modo test).
  - TennisGame: simula un juego (game) con el sistema 0–15–30–40–Ad.
  - TennisSet: simula un set completo, con o sin tiebreak.
  - TennisMatch: simula un partido completo al mejor de 3 o 5 sets.

Este módulo está libre de prints/interacción, listo para uso desde FastAPI.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

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
                 p1: Player, p2: Player):
        self.server = server
        self.returner = returner
        self.p1 = p1
        self.p2 = p2
        self.points = {SACADOR: 0, RESTADOR: 0}
        self.feed: List[PointResult] = []

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
        if s < 3 and r < 3:
            return self.point_names[self.points[SACADOR if player == self.server else RESTADOR]]
        if s >= 3 and r >= 3:
            if s == r:
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
            return SACADOR
        if r >= 4 and r >= s + 2:
            return RESTADOR
        return None

    def play(self, verbose: bool = False) -> str:
        """Juega un juego completo y devuelve el ganador ('SACADOR' o 'RESTADOR')."""
        while True:
            clutch = self.is_clutch_point()
            ps = PointSimulator(self.server, self.returner, clutch=clutch)

            res = ps.simulate(verbose=verbose)
            self.points[res.winner] += 1
            self.feed.append(res)

            # Actualizar estamina de ambos jugadores
            for jugador in [self.server, self.returner]:
                # Fatiga proporcional a la duración del punto e inversa al físico
                fatiga = 0.08 * (res.stats["rally_shots"] / 10) * (1 - jugador.Fisico / 100)
                jugador.Estamina = max(0.0, jugador.Estamina - fatiga)

            # === Actualizar momentum según el resultado del punto ===
            if res.winner == SACADOR:
                ganador, perdedor = self.server, self.returner
            else:
                ganador, perdedor = self.returner, self.server

            # Actualizar rachas
            ganador.streak = max(1, ganador.streak + 1)
            perdedor.streak = min(-1, perdedor.streak - 1)

            # Ajuste de momentum con saturación [-50, 50]
            ganador.Momentum = min(50.0, ganador.Momentum + 2 * abs(ganador.streak))
            perdedor.Momentum = max(-50.0, perdedor.Momentum - 2 * abs(perdedor.streak))

            # Relajación hacia 0 (tendencia a neutralidad)
            ganador.Momentum *= 0.97
            perdedor.Momentum *= 0.97

            winner = self.is_finished()
            if winner:
                # Actualizar estamina de ambos jugadores
                for jugador in [self.p1, self.p2]:
                    rec = 2 + 8 * (jugador.Fisico / 100)
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

    def __init__(self, player1: Player, player2: Player, target_points: int = 7):
        self.p1 = player1
        self.p2 = player2
        self.target_points = target_points
        self.points = {"P1": 0, "P2": 0}
        self.server_flag = 0  # alternancia de servicio (simplificada)
        self.feed = []

    def is_finished(self) -> Optional[str]:
        """Comprueba si el tie-break ha finalizado."""
        a, b = self.points["P1"], self.points["P2"]
        if (a >= self.target_points or b >= self.target_points) and abs(a - b) >= 2:
            return "P1" if a > b else "P2"
        return None

    def play(self, verbose: bool = False) -> str:
        """Juega el tie-break completo y devuelve el ganador ('P1' o 'P2')."""
        while True:
            # Alternar saque cada 2 puntos tras el primero
            if self.server_flag == 0:
                server, returner = self.p1, self.p2
            elif (self.server_flag - 1) % 4 < 2:
                server, returner = self.p2, self.p1
            else:
                server, returner = self.p1, self.p2

            ps = PointSimulator(server, returner, clutch=True)
            res = ps.simulate(verbose=verbose)
            winner_tag = "P1" if res.winner == SACADOR and server == self.p1 else "P2" if res.winner == SACADOR and server == self.p2 else ("P1" if res.winner == RESTADOR and returner == self.p1 else "P2")
            self.points[winner_tag] += 1
            self.feed.append(res)

            if verbose:
                print(f"Tie-break → {self.p1.name}: {self.points['P1']}, {self.p2.name}: {self.points['P2']}")

            self.server_flag += 1
            fin = self.is_finished()
            if fin:
                if verbose:
                    print(f"\n>>> TIE-BREAK ganado por {'Jugador 1' if fin == 'P1' else 'Jugador 2'} ({self.points['P1']}–{self.points['P2']}) <<<")
                return fin


# ============================================================
# Clase TennisSet
# ============================================================

class TennisSet:
    """Simula un set completo (con o sin tiebreak)."""

    def __init__(self, player1: Player, player2: Player,
                 tiebreak: bool = True):
        self.p1 = player1
        self.p2 = player2
        self.tiebreak = tiebreak
        self.games = {"P1": 0, "P2": 0}
        self.server_flag = 0  # alterna el sacador

    def is_finished(self) -> Optional[str]:
        g1, g2 = self.games["P1"], self.games["P2"]
        if self.tiebreak:
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
    
    def _is_decisive_set(self) -> bool:
        """Devuelve True si este set es el último del partido (para tie-break a 10)."""
        return False

    def play(self, verbose: bool = False) -> Tuple[str, Tuple[int, int]]:
        while True:
            server, returner = (self.p1, self.p2) if self.server_flag % 2 == 0 else (self.p2, self.p1)
            tag_server, tag_returner = ("P1", "P2") if self.server_flag % 2 == 0 else ("P2", "P1")

            game = TennisGame(server, returner, self.p1, self.p2)
            winner = game.play(verbose=verbose)

            if winner == SACADOR:
                self.games[tag_server] += 1
            else:
                self.games[tag_returner] += 1

            # ---- NUEVO BLOQUE: TIEBREAK REAL ----
            if self.tiebreak and self.games["P1"] == 6 and self.games["P2"] == 6:
                if verbose:
                    print("\n=== TIE-BREAK ===")
                tb_target = 10 if self._is_decisive_set() else 7
                tb = TieBreakGame(self.p1, self.p2, target_points=tb_target)
                tb_winner = tb.play(verbose=verbose)
                if tb_winner == "P1":
                    self.games["P1"] += 1
                else:
                    self.games["P2"] += 1

                # Recuperación larga tras set (post tie-break)
                for jugador in [self.p1, self.p2]:
                    rec_set = 10 + 20 * (jugador.Fisico / 100)
                    jugador.Estamina = min(100.0, jugador.Estamina + rec_set)

                return tb_winner, (self.games["P1"], self.games["P2"])
            # -------------------------------------

            self.server_flag += 1
            fin = self.is_finished()
            if fin:
                # Recuperación larga tras set normal
                for jugador in [self.p1, self.p2]:
                    rec_set = 10 + 20 * (jugador.Fisico / 100)
                    jugador.Estamina = min(100.0, jugador.Estamina + rec_set)

                # Bonus adicional de momentum por ganar/perder set
                for jugador in [self.p1, self.p2]:
                    if (fin == "P1" and jugador == self.p1) or (fin == "P2" and jugador == self.p2):
                        jugador.Momentum = min(50.0, jugador.Momentum + 15.0)
                    else:
                        jugador.Momentum = max(-50.0, jugador.Momentum - 15.0)

                return fin, (self.games["P1"], self.games["P2"])


# ============================================================
# Clase TennisMatch
# ============================================================

class TennisMatch:
    """Simula un partido completo al mejor de N sets."""

    def __init__(self, player1: Player, player2: Player,
                 best_of: int = 3, tiebreak: bool = True):
        self.p1 = player1
        self.p2 = player2
        self.best_of = best_of
        self.tiebreak = tiebreak
        self.sets = {"P1": 0, "P2": 0}
        self.resultados_sets: List[Tuple[int, int]] = []

        self.p1.reset_dynamic_state()
        self.p2.reset_dynamic_state()

    def is_finished(self) -> Optional[str]:
        needed = (self.best_of // 2) + 1
        if self.sets["P1"] >= needed:
            return "P1"
        if self.sets["P2"] >= needed:
            return "P2"
        return None

    def play(self, verbose: bool = False) -> str:
        """Juega el partido completo y devuelve el nombre del ganador."""
        set_num = 1
        while True:
            set_sim = TennisSet(self.p1, self.p2, tiebreak=self.tiebreak)
            ganador, marcador = set_sim.play(verbose=verbose)
            self.sets[ganador] += 1
            self.resultados_sets.append(marcador)

            fin = self.is_finished()
            if fin:
                return self.p1.name if fin == "P1" else self.p2.name
            set_num += 1
