# -*- coding: utf-8 -*-
import numpy as np
import random
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple

# -------------- Utilidades --------------

def clip(x, lo, hi):
    return max(lo, min(hi, x))

def rand():
    return random.random()

# -------------- Entidades básicas --------------

@dataclass
class Player:
    name: str
    # Habilidades (0..100)
    Primer_Saque: float
    Segundo_Saque: float
    Fisico: float
    Estamina: float
    Consistencia: float
    Clutch: float
    Momentum: float
    # Golpes
    Derecha: float
    Reves: float
    Resto: float
    Movilidad: float

    # Normalizados a 0..1 (propiedades para mantener legibilidad)
    @property
    def S1(self): return self.Primer_Saque/100.0
    @property
    def S2(self): return self.Segundo_Saque/100.0
    @property
    def F(self):  return self.Fisico/100.0
    @property
    def E(self):  return self.Estamina/100.0
    @property
    def C(self):  return self.Consistencia/100.0
    @property
    def K(self):  return self.Clutch/100.0
    @property
    def M(self):  return self.Momentum/100.0
    @property
    def FH(self): return self.Derecha/100.0
    @property
    def BH(self): return self.Reves/100.0
    @property
    def RET(self):return self.Resto/100.0
    @property
    def MOV(self):return self.Movilidad/100.0

    def pick_side(self) -> Tuple[str, float]:
        """Escoge derecha o revés con prob. proporcional a la habilidad."""
        p_fh = self.FH / (self.FH + self.BH + 1e-9)
        if rand() < p_fh:
            return "FH", self.FH
        return "BH", self.BH

# -------------- Estado de bola --------------

@dataclass
class Ball:
    pot: float   # [0..1]
    prec: float  # [0..1]
    side: str    # "FH" o "BH" del jugador que golpeó
    by: str      # "SACADOR" o "RESTADOR"

    @property
    def shotQ(self) -> float:
        # Dureza percibida de la bola entrante
        return clip(0.65*self.pot + 0.35*self.prec, 0.0, 1.0)

# -------------- Base de Golpe --------------

class Shot:
    def __init__(self, hitter: Player, receiver: Player, feed: List[str]):
        self.hitter = hitter
        self.receiver = receiver
        self.feed = feed

    # Polimórficas:
    def attempt_reach(self, incoming: Optional[Ball]) -> Tuple[bool, float]:
        """Probabilidad de que el receptor alcance la bola."""
        raise NotImplementedError

    def produce_ball(self, incoming: Optional[Ball]) -> Tuple[Optional[Ball], Dict]:
        """Genera la bola saliente si se alcanzó, o None si error directo."""
        raise NotImplementedError

# -------------- Saque (1º/2º) --------------

class Serve(Shot):
    def _prob_in_first(self, pot, prec) -> float:
        # Fórmula acordada (rango aprox 0.50-0.75)
        p = pot; q = prec
        s = self.hitter.S1; c = self.hitter.C
        score = 0.6*q - 0.3*p + 0.2*s + 0.2*c
        score = clip((score + 0.3)/1.3, 0, 1)
        return 0.5 + 0.25*score

    def _prob_in_second(self, pot, prec) -> float:
        s = self.hitter.S2; c = self.hitter.C
        delta_clutch = ((self.hitter.K - 0.5)/0.5)/100 if False else 0  # punto_clave opcional
        delta_momentum = (self.hitter.M/0.5)/100
        score = 0.6*s + 0.4*c
        return 0.86 + 0.09*score + delta_clutch + delta_momentum

    def _sample_pot_prec_first(self):
        j = self.hitter
        pot_base = 0.5*j.S1 + 0.35*j.F + 0.15*j.E
        sig_pot = 0.04 + 0.08*(1-j.C) + 0.04*(1-j.E)
        pot = clip(np.random.normal(pot_base, sig_pot), 0.01, 1.0)

        prec_base = 0.42*j.S1 + 0.38*j.C + 0.20*j.E
        sig_prec = 0.05 + 0.10*(1-j.C) + 0.05*(1-j.E)
        prec = clip(np.random.normal(prec_base, sig_prec), 0.01, 1.0)
        return pot, prec

    def _sample_pot_prec_second(self, pot1):
        j = self.hitter
        pot_base = 0.5*j.S2 + 0.35*j.F + 0.15*j.E
        sig_pot = 0.02 + 0.04*(1-j.C) + 0.02*(1-j.E)
        pot = clip(np.random.normal(pot_base, sig_pot), 0.01, 1.0)
        r = random.uniform(0.70, 0.80)
        pot = clip(pot*r + random.uniform(-0.02,0.02), max(0.7*pot1,0.50), min(0.8*pot1,0.66))

        prec_base = 0.42*j.S2 + 0.38*j.C + 0.20*j.E
        sig_prec = 0.025 + 0.10*(1-j.C) + 0.05*(1-j.E)
        prec = clip(np.random.normal(prec_base, sig_prec), 0.01, 1.0)
        return pot, prec

    def serve_sequence(self) -> Tuple[Optional[Ball], Dict]:
        pot1, prec1 = self._sample_pot_prec_first()
        p_in1 = self._prob_in_first(pot1, prec1)
        in1 = rand() < p_in1

        log = {
            "first": {"pot": pot1, "prec": prec1, "p_in": p_in1, "in": in1},
            "second": None, "ace": False, "double_fault": False
        }
        self.feed.append(
            f"{self.hitter.name} realiza primer saque: Pot={pot1:.2f}, Prec={prec1:.2f}, p_in={p_in1:.2f} → {'IN' if in1 else 'FALTA'}"
        )

        if in1:
            ball = Ball(pot=pot1, prec=prec1, side="S", by=self.hitter.name)
            return ball, log

        pot2, prec2 = self._sample_pot_prec_second(pot1)
        p_in2 = self._prob_in_second(pot2, prec2)
        in2 = rand() < p_in2
        log["second"] = {"pot": pot2, "prec": prec2, "p_in": p_in2, "in": in2}
        self.feed.append(
            f"{self.hitter.name} realiza segundo saque: Pot={pot2:.2f}, Prec={prec2:.2f}, p_in={p_in2:.2f} → {'IN' if in2 else 'FALTA'}"
        )

        if in2:
            ball = Ball(pot=pot2, prec=prec2, side="S", by=self.hitter.name)
            return ball, log

        log["double_fault"] = True
        return None, log

# -------------- Resto --------------

class ReturnShot(Shot):
    # Prob. de alcanzar el saque
    def attempt_reach(self, incoming: Ball, isFirst: bool) -> Tuple[bool, float]:
        dif = clip(0.7*incoming.pot + 0.3*incoming.prec, 0.0, 1.0)
        cap = 0.5*self.receiver.RET + 0.3*self.receiver.MOV + 0.2*self.receiver.E
        delta_second = 0.1 if not isFirst else 0
        pr = clip(0.85 + (cap - dif)*0.25 + delta_second, 0.70, 0.97)
        ok = rand() < pr
        self.feed.append(
            f"   {self.receiver.name} intenta alcanzar el saque → pr={pr:.2f} (dif={dif:.2f}), cap={cap:.2f}) → {'ALCANZADO' if ok else 'NO LLEGA'}"
        )
        return ok, pr

    # Genera bola de resto (si alcanzó)
    def produce_ball(self, incoming: Ball) -> Tuple[Optional[Ball], Dict]:
        hitter = self.receiver
        side_name, side = hitter.pick_side()
        # Base del resto
        pot_base = 0.35*hitter.RET + 0.25*hitter.F + 0.20*hitter.E + 0.20*side
        prec_base = 0.40*hitter.RET + 0.25*hitter.C + 0.20*side + 0.15*hitter.MOV

        shotQ_in = incoming.shotQ
        pot_star = pot_base + 0.18*(0.50 - shotQ_in)
        prec_star = prec_base + 0.22*(0.60 - shotQ_in)

        pot_star = clip(pot_star, 0.15, 0.75)
        prec_star = clip(prec_star, 0.20, 0.92)

        # Ruido (menos si está más consistente/descansado)
        sigma_p = clip(0.03 + 0.04*pot_star - 0.02*hitter.E, 0.01, 0.10)
        sigma_r = clip(0.02 + 0.03*prec_star - 0.01*hitter.E, 0.01, 0.10)
        pot_out = clip(np.random.normal(pot_star, sigma_p), 0.10, 0.95)
        prec_out = clip(np.random.normal(prec_star, sigma_r), 0.10, 0.97)

        # Probabilidad de meter el resto
        Q = 0.6*hitter.RET + 0.4*hitter.C
        Q_adj = Q - 0.5*(shotQ_in - 0.5)
        p_in = clip(0.65 + 0.3*(Q_adj - 0.5), 0.05, 0.99)
        eps = np.random.normal(0, 0.05*(1-hitter.C))
        p_final = clip(p_in + eps, 0.02, 0.99)
        in_flag = rand() < p_final

        self.feed.append(
            f"{hitter.name} golpea ({side_name}) → Pot={pot_out:.2f}, Prec={prec_out:.2f}, p_in={p_final:.2f} → {'DENTRO' if in_flag else 'FUERA'}"
        )

        if not in_flag:
            return None, {"side": side_name, "pot": pot_out, "prec": prec_out, "p_in": p_final, "in": False}

        ball = Ball(pot=pot_out, prec=prec_out, side=side_name, by="RESTADOR")
        return ball, {"side": side_name, "pot": pot_out, "prec": prec_out, "p_in": p_final, "in": True}

# -------------- Golpe de rally --------------

class RallyShot(Shot):
    def attempt_reach(self, incoming: Ball) -> Tuple[bool, float]:
        shotQ = incoming.shotQ
        mov = self.receiver.MOV
        who = self.hitter
        est = self.receiver.E
        pr = clip(0.72 + 0.30*(mov - 0.70) + 0.20*(est - 0.70) - 0.55*(shotQ - 0.60), 0.02, 0.98)
        ok = rand() < pr
        self.feed.append(
            f"   {who.name} → prob. alcanzar bola={pr:.2f} (shotQ_in={shotQ:.2f}) → {'ALCANZADO' if ok else 'NO LLEGA'}"
        )
        return ok, pr

    def produce_ball(self, incoming: Ball) -> Tuple[Optional[Ball], Dict]:
        hitter = self.hitter 
        side_name, side = hitter.pick_side()

        pot_base = 0.45*hitter.F + 0.25*hitter.E + 0.20*side + 0.10*hitter.C
        prec_base = 0.40*hitter.C + 0.30*side + 0.20*hitter.MOV + 0.10*hitter.E

        shotQ_in = incoming.shotQ
        pot_star = pot_base + 0.18*(0.50 - shotQ_in)
        prec_star = prec_base + 0.22*(0.60 - shotQ_in)
        pot_star = clip(pot_star, 0.15, 0.75)
        prec_star = clip(prec_star, 0.20, 0.92)

        sigma_p = clip(0.03 + 0.04*pot_star - 0.02*hitter.E, 0.01, 0.10)
        sigma_r = clip(0.02 + 0.03*prec_star - 0.01*hitter.E, 0.01, 0.10)
        pot_out = clip(np.random.normal(pot_star, sigma_p), 0.10, 0.95)
        prec_out = clip(np.random.normal(prec_star, sigma_r), 0.10, 0.97)

        A = side
        Q = 0.6*A + 0.4*hitter.C
        Q_adj = Q - 0.5*(shotQ_in - 0.5)
        p_in = clip(0.65 + 0.3*(Q_adj - 0.5), 0.05, 0.99)
        eps = np.random.normal(0, 0.05*(1-hitter.C))
        p_final = clip(p_in + eps, 0.02, 0.99)
        in_flag = rand() < p_final

        self.feed.append(
            f"{hitter.name} golpea ({side_name}) → Pot={pot_out:.2f}, Prec={prec_out:.2f}, p_in={p_in:.2f} → {'DENTRO' if in_flag else 'FUERA'}"
        )

        if not in_flag:
            return None, {"side": side_name, "pot": pot_out, "prec": prec_out, "p_in": p_final, "in": False}

        ball = Ball(pot=pot_out, prec=prec_out, side=side_name, by=hitter.name)
        return ball, {"side": side_name, "pot": pot_out, "prec": prec_out, "p_in": p_final, "in": True}

# -------------- Simulador de Punto --------------

@dataclass
class PointResult:
    winner: str
    reason: str
    feed: List[str] = field(default_factory=list)
    stats: Dict = field(default_factory=dict)

class PointSimulator:
    def __init__(self, server: Player, returner: Player, max_rally_shots: int = 40):
        self.S = server
        self.R = returner
        self.max_rally_shots = max_rally_shots

    def simulate(self, verbose=True) -> PointResult:
        feed: List[str] = []
        stats = {
            "aces": 0, "double_faults": 0,
            "first_in": 0, "first_total": 0,
            "second_in": 0, "second_total": 0,
            "rally_shots": 0
        }

        # 1) Saque
        srv = Serve(self.S, self.R, feed)
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
            return PointResult(winner="RESTADOR", reason="doble_falta", feed=feed, stats=stats)

        # 2) Resto (si el saque entró)
        ret = ReturnShot(self.S, self.R, feed)
        ok, pr_reach = ret.attempt_reach(ball, isFirst)
        if not ok:
            stats["aces"] += 1
            feed.append(">>> Resultado: ACE")
            return PointResult(winner="SACADOR", reason="ace", feed=feed, stats=stats)

        ball, rlog = ret.produce_ball(ball)
        if ball is None:
            feed.append(">>> Resultado: ERROR DE RESTO")
            return PointResult(winner="SACADOR", reason="error_resto", feed=feed, stats=stats)

        # 3) Rally
        hitter = self.S   # quien recibe ahora la bola es el sacador
        receiver = self.S  # placeholder para claridad
        current_by = "SACADOR"

        for turn in range(self.max_rally_shots):
            stats["rally_shots"] += 1
            # alternar: quien golpea es el que NO envió la bola anterior
            if ball.by in ("SACADOR", "RALLY_S"):   # bola viene del sacador → golpea restador
                hitter_obj = self.R
                other_obj = self.S
                tag_prev = "SACADOR"
            else:
                hitter_obj = self.S
                other_obj = self.R
                tag_prev = "RESTADOR"

            rally = RallyShot(hitter_obj, other_obj, feed)
            ok, pr = rally.attempt_reach(ball)
            if not ok:
                feed.append(f">>> Resultado: PUNTO para {tag_prev} (no llega)")
                return PointResult(winner=tag_prev, reason="no_llega", feed=feed, stats=stats)

            ball2, log = rally.produce_ball(ball)
            if ball2 is None:
                feed.append(f">>> Resultado: PUNTO para {tag_prev} (falla golpe)")
                return PointResult(winner=tag_prev, reason="error_golpe", feed=feed, stats=stats)

            # pasar bola; marcar origen para alternar
            ball = ball2
            ball.by = "RALLY_R" if tag_prev == "SACADOR" else "RALLY_S"

        feed.append(">>> Punto cortado por límite de rally (empate técnico)")
        return PointResult(winner="NINGUNO", reason="max_rally", feed=feed, stats=stats)

# ---------------- MATCH SIMULATOR ----------------

@dataclass
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
    reasons: Dict[str,int] = field(default_factory=lambda: {})
    points_feed: List[PointResult] = field(default_factory=list)

    def add_point(self, res: "PointResult"):
        self.total_points += 1
        if res.winner == "SACADOR":
            self.server_points_won += 1
        elif res.winner == "RESTADOR":
            self.returner_points_won += 1

        # Saques
        self.first_in += res.stats["first_in"]
        self.first_total += res.stats["first_total"]
        self.second_in += res.stats["second_in"]
        self.second_total += res.stats["second_total"]

        self.aces += res.stats["aces"]
        self.double_faults += res.stats["double_faults"]

        self.rally_shots.append(res.stats["rally_shots"])
        self.reasons[res.reason] = self.reasons.get(res.reason,0)+1

        self.points_feed.append(res)  # 🔥 guardamos todo el detalle del punto

    def resumen_detallado(self):
        print("\n========== RESUMEN DETALLADO DE PUNTOS ==========")
        for i, res in enumerate(self.points_feed, 1):
            print(f"\n--- Punto {i} ---")
            for line in res.feed:
                print(" ", line)
            print(f" >>> Ganador: {res.winner} (Motivo: {res.reason})")

    def resumen_global(self):
        print("\n========== ESTADÍSTICAS GENERALES ==========")
        print(f"Total puntos jugados: {self.total_points}")
        print(f"Puntos ganados por el SACADOR: {self.server_points_won} ({100*self.server_points_won/self.total_points:.2f}%)")
        print(f"Puntos ganados por el RESTADOR: {self.returner_points_won} ({100*self.returner_points_won/self.total_points:.2f}%)")

        # Saques
        if self.first_total>0:
            pct1 = 100*self.first_in/self.first_total
            print(f"Primeros saques dentro: {self.first_in}/{self.first_total} ({pct1:.2f}%)")
        if self.second_total>0:
            pct2 = 100*self.second_in/self.second_total
            print(f"Segundos saques dentro: {self.second_in}/{self.second_total} ({pct2:.2f}%)")

        print(f"Aces: {self.aces} ({100*self.aces/self.total_points:.2f}%)")
        print(f"Dobles faltas: {self.double_faults} ({100*self.double_faults/self.total_points:.2f}%)")

        # Duración media puntos
        if self.rally_shots:
            avg_len = np.mean(self.rally_shots)
            print(f"Duración media de puntos (golpes de rally): {avg_len:.2f}")

        # Formas de acabar puntos
        print("\n--- Motivos de finalización ---")
        for k,v in self.reasons.items():
            print(f"{k}: {v} ({100*v/self.total_points:.1f}%)")

# ---------------- MATCH SIMULATOR ----------------

class MatchSimulator:
    def __init__(self, server: Player, returner: Player, max_rally_shots: int = 40):
        self.server = server
        self.returner = returner
        self.max_rally_shots = max_rally_shots

    def simulate_points(self, n: int, verbose: bool = False) -> MatchStats:
        stats = MatchStats()
        for i in range(1,n+1):
            ps = PointSimulator(self.server, self.returner, self.max_rally_shots)
            res = ps.simulate(verbose=verbose)
            stats.add_point(res)
        return stats

# ---------------- GAME & SET SIMULATOR ----------------

class TennisGame:
    point_names = ["0", "15", "30", "40", "Ad"]

    def __init__(self, server: Player, returner: Player, p1: Player, p2: Player, max_rally_shots: int = 40):
        self.server = server
        self.returner = returner
        self.p1 = p1
        self.p2 = p2
        self.max_rally_shots = max_rally_shots
        self.points = {"SACADOR": 0, "RESTADOR": 0}
        self.feed = []

    def get_point_label(self, player: Player) -> str:
        """Devuelve '0','15','30','40','Ad' según la situación real del juego."""
        s, r = self.points["SACADOR"], self.points["RESTADOR"]

        # Caso normal (sin deuce)
        if s < 3 and r < 3:
            if player == self.server:
                return self.point_names[s]
            else:
                return self.point_names[r]

        # Deuce o más allá
        if s >= 3 and r >= 3:
            if s == r:
                return "40"
            elif s == r + 1:
                return "Ad" if player == self.server else "40"
            elif r == s + 1:
                return "Ad" if player == self.returner else "40"
            else:
                return "40"

        # Si uno llegó a 4 sin igualdad
        if player == self.server:
            return self.point_names[min(s, 4)]
        else:
            return self.point_names[min(r, 4)]

    def print_scoreboard(self, set_results: list[tuple[int, int]], current_games: tuple[int, int]):
        """Muestra el marcador completo tipo TV."""
        p1_sets = " ".join([f"[{a}]" for a, _ in set_results])
        p2_sets = " ".join([f"[{b}]" for _, b in set_results])

        print("\n===== MARCADOR =====")
        print(f"Sacador actual: {self.server.name}")
        print("------------------------------------------------")
        print(f"{'Jugador':<15}{'Sets':>12}{'Juegos':>10}{'Puntos':>10}")
        print("------------------------------------------------")

        p1_points = self.get_point_label(self.p1)
        p2_points = self.get_point_label(self.p2)
        p1_marker = " (S)" if self.p1 == self.server else ""
        p2_marker = " (S)" if self.p2 == self.server else ""

        print(f"{self.p1.name:<15}{p1_sets:>12}{current_games[0]:>10}{p1_points:>10}{p1_marker}")
        print(f"{self.p2.name:<15}{p2_sets:>12}{current_games[1]:>10}{p2_points:>10}{p2_marker}")
        print("------------------------------------------------")

    def is_finished(self) -> Optional[str]:
        s, r = self.points["SACADOR"], self.points["RESTADOR"]
        if s >= 4 and s >= r + 2:
            return "SACADOR"
        if r >= 4 and r >= s + 2:
            return "RESTADOR"
        return None

    def play(self, verbose=True, set_results=None, current_games=(0, 0)) -> str:
        if set_results is None:
            set_results = []
        while True:
            ps = PointSimulator(self.server, self.returner, self.max_rally_shots)
            res = ps.simulate(verbose=False)
            self.points[res.winner] += 1
            self.feed.append(res)

            if verbose:
                print("\n--- Nuevo punto ---")
                for line in res.feed:
                    print(" ", line)
                print(f">>> Punto para {res.winner} ({res.reason})")

                self.print_scoreboard(set_results, current_games)
                input("Presiona ENTER para continuar...\n")

            winner = self.is_finished()
            if winner:
                ganador = self.server.name if winner == "SACADOR" else self.returner.name
                if verbose:
                    print(f"\n>>> JUEGO para {ganador} <<<")
                return winner



class TennisSet:
    def __init__(self, player1: Player, player2: Player, max_rally_shots=40, tiebreak=True):
        self.p1 = player1
        self.p2 = player2
        self.max_rally_shots = max_rally_shots
        self.tiebreak = tiebreak
        self.games = {"P1": 0, "P2": 0}
        self.server_flag = 0

    def is_finished(self) -> Optional[str]:
        g1, g2 = self.games["P1"], self.games["P2"]
        if self.tiebreak:
            if (g1 >= 6 or g2 >= 6) and abs(g1 - g2) >= 2:
                return "P1" if g1 > g2 else "P2"
            if g1 == 7 and g2 == 6:
                return "P1"
            if g2 == 7 and g1 == 6:
                return "P2"
        else:
            if g1 >= 6 and g1 >= g2 + 2:
                return "P1"
            if g2 >= 6 and g2 >= g1 + 2:
                return "P2"
        return None

    def play(self, verbose=True, set_results=None) -> tuple[str, tuple[int, int]]:
        if set_results is None:
            set_results = []

        while True:
            server, returner = (self.p1, self.p2) if self.server_flag % 2 == 0 else (self.p2, self.p1)
            tag_server, tag_returner = ("P1", "P2") if self.server_flag % 2 == 0 else ("P2", "P1")

            if verbose:
                print(f"\n=== Nuevo juego (saca {server.name}) ===")

            game = TennisGame(server, returner, self.p1, self.p2, self.max_rally_shots)
            winner = game.play(verbose=verbose, set_results=set_results,
                               current_games=(self.games["P1"], self.games["P2"]))

            if winner == "SACADOR":
                self.games[tag_server] += 1
            else:
                self.games[tag_returner] += 1

            if verbose:
                print(f"Marcador del set: {self.p1.name} {self.games['P1']} - {self.p2.name} {self.games['P2']}")

            self.server_flag += 1
            fin = self.is_finished()
            if fin:
                ganador_nombre = self.p1.name if fin == "P1" else self.p2.name
                if verbose:
                    print(f"\n>>> SET para {ganador_nombre} ({self.games['P1']}–{self.games['P2']}) <<<")
                return fin, (self.games["P1"], self.games["P2"])


class TennisMatch:
    def __init__(self, player1: Player, player2: Player, max_rally_shots=40, best_of=3, tiebreak=True):
        self.p1 = player1
        self.p2 = player2
        self.max_rally_shots = max_rally_shots
        self.best_of = best_of
        self.tiebreak = tiebreak
        self.sets = {"P1": 0, "P2": 0}
        self.resultados_sets: list[tuple[int, int]] = []

    def is_finished(self) -> Optional[str]:
        needed = (self.best_of // 2) + 1
        if self.sets["P1"] >= needed:
            return "P1"
        if self.sets["P2"] >= needed:
            return "P2"
        return None

    def play(self, verbose=True) -> str:
        set_num = 1
        while True:
            if verbose:
                print(f"\n===== SET {set_num} =====")

            set_sim = TennisSet(self.p1, self.p2, self.max_rally_shots, tiebreak=self.tiebreak)
            ganador, marcador = set_sim.play(verbose=verbose, set_results=self.resultados_sets)
            self.sets[ganador] += 1
            self.resultados_sets.append(marcador)

            if verbose:
                marcador_str = " ".join([f"[{a}-{b}]" for a, b in self.resultados_sets])
                print(f"Marcador global de sets: {self.p1.name} vs {self.p2.name} → {marcador_str}")

            fin = self.is_finished()
            if fin:
                ganador_nombre = self.p1.name if fin == "P1" else self.p2.name
                if verbose:
                    print(f"\n>>> PARTIDO para {ganador_nombre} <<<")
                    marcador_final = " ".join([f"[{a}-{b}]" for a, b in self.resultados_sets])
                    print(f"Marcadores de sets: {marcador_final}")
                return ganador_nombre
            set_num += 1


# ---------------- EJEMPLO DE USO ----------------
if __name__ == "__main__":
    # Jugador 1
    player1 = Player(
        name="Alcaraz",
        Primer_Saque = 80,   # muy sólido pero no un cañonero tipo Isner
        Segundo_Saque = 80,  # consistente y con efecto, raro que falle
        Fisico = 80,         # uno de los mejores físicamente del circuito
        Estamina = 80,       # aguanta partidos largos sin apenas caída
        Consistencia = 80,   # algo irregular en fases, pero estable en general
        Clutch = 80,         # sube el nivel en momentos importantes
        Momentum = 0,        # (neutro para simular de inicio)
        Derecha = 80,        # golpe estrella, ganador en cualquier situación
        Reves = 80,          # sólido, buena defensa y ritmo
        Resto = 80,          # resta bien incluso a grandes sacadores
        Movilidad = 80       # brutal en desplazamientos y reflejos
    )


    # Jugador 2
    player2 = Player(
        name="Sinner",
        Primer_Saque = 80,   # muy buen primer servicio
        Segundo_Saque = 80,  # correcto, pero algo menos seguro que Alcaraz
        Fisico = 80,         # fuerte y estable físicamente
        Estamina = 80,       # muy buena resistencia en intercambios largos
        Consistencia = 80,   # más regular que Alcaraz
        Clutch = 80,         # no tan emocional ni explosivo, pero fiable
        Momentum = 0,
        Derecha = 80,        # plana, potente y muy efectiva
        Reves = 80,          # uno de los mejores del mundo
        Resto = 80,          # resta profundo y sólido
        Movilidad = 80       # buena pero menos elástica que la de Alcaraz
    )


    # Partido
    match = TennisMatch(player1, player2, max_rally_shots=60, best_of=5, tiebreak=True)
    ganador = match.play(verbose=True)

    print("\n=== RESULTADO FINAL DEL PARTIDO ===")
    print(f"Ganador: {ganador}")
    print(f"Sets: {match.sets['P1']}–{match.sets['P2']}")
    print("Marcadores por set:", match.resultados_sets)
