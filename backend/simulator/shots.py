# backend/simulator/shots.py
"""
Módulo de golpes (Shots) del simulador ADAF Tennis Simulator.
Incluye las clases para el saque, el resto y los peloteos.
Define las clases de golpes: Serve, ReturnShot y RallyShot.
"""


from __future__ import annotations
import random
import numpy as np
from typing import Optional, Tuple, Dict, List

from .models import Player, Ball
from .utils import clip, rand, SACADOR, RESTADOR


# ============================================================
# Clase base generica
# ============================================================

class Shot:
    """
    Clase base para los diferentes tipos de golpes.
    Contiene referencias al jugador que golpea (hitter) y al rival (receiver),
    así como un registro opcional de eventos (feed).
    
    Si se pasa un dict `strategy` con multiplicadores, estos se aplican
    después de los cálculos base (Modo Estratégico).
    """

    def __init__(self, hitter: Player, receiver: Player, feed: Optional[List[str]] = None,
                 clutch: bool = False, strategy: Optional[Dict[str, float]] = None):
        self.hitter = hitter
        self.receiver = receiver
        self.feed = feed if feed is not None else []
        self.clutch = clutch
        self.strategy = strategy  # multiplicadores de estrategia (o None)

    # --- Helpers de estrategia ---
    def _sm(self, key: str, default: float = 1.0) -> float:
        """Devuelve el multiplicador de estrategia para `key`, o `default` si no hay estrategia."""
        if self.strategy is None:
            return default
        return self.strategy.get(key, default)

    def log(self, text: str):
        """Añade una línea al feed si está activo."""
        if self.feed is not None:
            self.feed.append(text)


# ============================================================
# Clase Serve (Saque)
# ============================================================

class Serve(Shot):
    """
    Saque (Serve) con las fórmulas EXACTAS acordadas:
      - Probabilidad de meter el primer saque:
        p_in1 = 0.5 + 0.25*Score
        con Score = clip((0.6*q - 0.3*p + 0.2*S1 + 0.2*C + 0.3)/1.3, 0, 1)
      - Probabilidad de meter el segundo saque:
        p_in2 = 0.86 + 0.09*(0.6*S2 + 0.4*C) + delta_clutch + delta_momentum
      - Muestreos normales de potencia y precisión dependientes de atributos:
        Primer saque:
          pot_base  = 0.5*S1 + 0.35*F + 0.15*E
          prec_base = 0.42*S1 + 0.38*C + 0.20*E
        Segundo saque:
          pot_base  = 0.5*S2 + 0.35*F + 0.15*E
          prec_base = 0.42*S2 + 0.38*C + 0.20*E
      - Desviaciones típicas (ruido) dependientes de la consistencia y estamina:
        desv_p (1º) = 0.04 + 0.08*(1 - C) + 0.04*(1 - E)
        desv_p (2º) = 0.02 + 0.04*(1 - C) + 0.02*(1 - E)
        desv_q (1º) = 0.05 + 0.10*(1 - C) + 0.05*(1 - E)
        desv_q (2º) = 0.025 + 0.10*(1 - C) + 0.05*(1 - E)
      - Ajuste adicional del segundo saque:
        pot2 = clip(pot2*r + ε, max(0.7*pot1, 0.50), min(0.8*pot1, 0.66))
        con r ∈ [0.70, 0.80] y ε ∈ [-0.02, +0.02]
    """

    def _prob_in_first(self, pot: float, prec: float) -> float:
        """Probabilidad de meter el primer saque (sin clutch)."""
        p = pot; q = prec
        s = self.hitter.S1; c = self.hitter.C
        score = 0.6*q - 0.3*p + 0.2*s + 0.2*c
        score = clip((score + 0.3)/1.3, 0, 1)
        return 0.5 + 0.25*score

    def _prob_in_second(self, pot: float, prec: float) -> float:
        """Probabilidad de meter el segundo saque (con posible efecto clutch)."""
        s = self.hitter.S2
        c = self.hitter.C

        # Base
        score = 0.6*s + 0.4*c
        base_prob = 0.86 + 0.09*score

        # --- Efecto Clutch (solo en puntos de presion) ---
        if self.clutch:
            k = self.hitter.K  # 0..1
            clutch_boost = (k - 0.5) * 0.20  # ±10% efecto
        else:
            clutch_boost = 0.0

        # --- Efecto Momentum ---
        m = self.hitter.Momentum / 100  # [-0.5, +0.5]
        momentum_boost = 0.05 * m       # ±5%

        p_final = base_prob * (1.0 + clutch_boost + momentum_boost)
        p_final *= self._sm("p_in_mult")
        return clip(p_final, 0.0, 1.0)

    def _sample_pot_prec_first(self) -> Tuple[float, float]:
        j = self.hitter
        pot_base = 0.5*j.S1 + 0.35*j.F + 0.15*j.E
        sig_pot  = 0.04 + 0.08*(1-j.C) + 0.04*(1-j.E)
        sig_pot *= self._sm("sigma_pot_mult")
        pot = clip(np.random.normal(pot_base, sig_pot), 0.01, 1.0)

        prec_base = 0.42*j.S1 + 0.38*j.C + 0.20*j.E
        sig_prec  = 0.05 + 0.10*(1-j.C) + 0.05*(1-j.E)
        sig_prec *= self._sm("sigma_prec_mult")
        prec = clip(np.random.normal(prec_base, sig_prec), 0.01, 1.0)

        # --- Ajuste por momentum ---
        m = self.hitter.Momentum / 100
        momentum_factor = 1.0 + 0.15 * m
        pot *= momentum_factor
        prec *= momentum_factor

        # --- Estrategia ---
        pot *= self._sm("pot_mult")
        prec *= self._sm("prec_mult")

        pot = clip(pot, 0.01, 1.0)
        prec = clip(prec, 0.01, 1.0)
        return pot, prec

    def _sample_pot_prec_second(self, pot1: float) -> Tuple[float, float]:
        j = self.hitter
        pot_base = 0.5*j.S2 + 0.35*j.F + 0.15*j.E
        sig_pot  = 0.02 + 0.04*(1-j.C) + 0.02*(1-j.E)
        sig_pot *= self._sm("sigma_pot_mult")
        pot = clip(np.random.normal(pot_base, sig_pot), 0.01, 1.0)
        r = random.uniform(0.70, 0.80)
        pot = clip(pot*r + random.uniform(-0.02, 0.02),
                   max(0.7*pot1, 0.50), min(0.8*pot1, 0.66))

        prec_base = 0.42*j.S2 + 0.38*j.C + 0.20*j.E
        sig_prec  = 0.025 + 0.10*(1-j.C) + 0.05*(1-j.E)
        sig_prec *= self._sm("sigma_prec_mult")
        prec = clip(np.random.normal(prec_base, sig_prec), 0.01, 1.0)

        # --- Ajuste por momentum ---
        m = self.hitter.Momentum / 100
        momentum_factor = 1.0 + 0.15 * m
        pot *= momentum_factor
        prec *= momentum_factor

        # --- Ajuste por clutch (solo si el punto es de presion) ---
        if self.clutch:
            k = self.hitter.K
            clutch_boost = 1.0 + (k - 0.5) * 0.20  # ±10 %
            prec *= clutch_boost

        # --- Estrategia ---
        pot *= self._sm("pot_mult")
        prec *= self._sm("prec_mult")

        pot = clip(pot, 0.01, 1.0)
        prec = clip(prec, 0.01, 1.0)
        return pot, prec

    def serve_sequence(self) -> Tuple[Optional[Ball], Dict]:
        """Ejecuta la secuencia de primer y segundo saque."""
        pot1, prec1 = self._sample_pot_prec_first()
        p_in1 = self._prob_in_first(pot1, prec1)
        in1 = rand() < p_in1

        log = {
            "first": {"pot": pot1, "prec": prec1, "p_in": p_in1, "in": in1},
            "second": None, "ace": False, "double_fault": False
        }
        self.log(
            f"{self.hitter.name} realiza primer saque: Pot={pot1:.2f}, Prec={prec1:.2f}, p_in={p_in1:.2f} → {'IN' if in1 else 'FALTA'}"
        )

        if in1:
            ball = Ball(pot=pot1, prec=prec1, side="S", by=SACADOR)
            return ball, log

        pot2, prec2 = self._sample_pot_prec_second(pot1)
        p_in2 = self._prob_in_second(pot2, prec2)
        in2 = rand() < p_in2
        log["second"] = {"pot": pot2, "prec": prec2, "p_in": p_in2, "in": in2}
        self.log(
            f"{self.hitter.name} realiza segundo saque{' (CLUTCH)' if self.clutch else ''}: "
            f"Pot={pot2:.2f}, Prec={prec2:.2f}, p_in={p_in2:.2f} → {'IN' if in2 else 'FALTA'}"
        )

        if in2:
            ball = Ball(pot=pot2, prec=prec2, side="S", by=SACADOR)
            return ball, log

        log["double_fault"] = True
        return None, log


# ============================================================
# Clase ReturnShot (Resto)
# ============================================================

class ReturnShot(Shot):
    """
    Resto (Return) con las fórmulas EXACTAS acordadas:
      - Probabilidad de alcanzar el saque:
        pr = clip(0.85 + (cap - dif)*0.25 + delta_second, 0.70, 0.97)
        con cap = 0.5*RET + 0.3*MOV + 0.2*E y dif = 0.7*pot + 0.3*prec
      - Potencia y precisión base del resto:
        pot_base = 0.35*RET + 0.25*F + 0.20*E + 0.20*side
        prec_base = 0.40*RET + 0.25*C + 0.20*side + 0.15*MOV
      - Ajuste según la calidad del saque recibido:
        pot* = pot_base + 0.18*(0.50 - shotQ_in)
        prec* = prec_base + 0.22*(0.60 - shotQ_in)
      - Probabilidad final de meter el resto:
        p_in = clip(0.65 + 0.3*(Q_adj - 0.5), 0.05, 0.99)
        con Q_adj = (0.6*RET + 0.4*C) - 0.5*(shotQ_in - 0.5)
      - Ruido aleatorio dependiente de la consistencia y estamina:
        desv_p = 0.03 + 0.04*pot* - 0.02*E
        desv_r = 0.02 + 0.03*prec* - 0.01*E
    """

    def attempt_reach(self, incoming: Ball, isFirst: bool) -> Tuple[bool, float]:
        """Evalúa si el restador logra alcanzar el saque."""
        dif = clip(0.7 * incoming.pot + 0.3 * incoming.prec, 0.0, 1.0)
        cap = 0.5 * self.receiver.RET + 0.3 * self.receiver.MOV + 0.2 * self.receiver.E
        delta_second = 0.1 if not isFirst else 0.0

        pr = clip(0.85 + (cap - dif) * 0.25 + delta_second, 0.70, 0.97)

        # --- Momentum mejora ligeramente la capacidad de llegar ---
        m = self.receiver.Momentum / 100
        pr *= (1.0 + 0.05 * m)

        # --- Estrategia: reach_mult ---
        pr *= self._sm("reach_mult")
        pr = clip(pr, 0.02, 0.98)

        ok = rand() < pr

        self.feed.append(
            f"   {self.receiver.name} intenta alcanzar el saque → pr={pr:.2f} (dif={dif:.2f}), cap={cap:.2f} → {'ALCANZADO' if ok else 'NO LLEGA'}"
        )
        return ok, pr

    def produce_ball(self, incoming: Ball) -> Tuple[Optional[Ball], Dict]:
      """Genera la bola de resto si alcanzó el saque."""
      hitter = self.receiver
      side_name, side = hitter.pick_side()

      # === Calculo base ===
      pot_base = 0.35 * hitter.RET + 0.25 * hitter.F + 0.20 * hitter.E + 0.20 * side
      prec_base = 0.40 * hitter.RET + 0.25 * hitter.C + 0.20 * side + 0.15 * hitter.MOV

      shotQ_in = incoming.shotQ
      pot_star = clip(pot_base + 0.18 * (0.50 - shotQ_in), 0.15, 0.75)
      prec_star = clip(prec_base + 0.22 * (0.60 - shotQ_in), 0.20, 0.92)

      sigma_p = clip(0.03 + 0.04 * pot_star - 0.02 * hitter.E, 0.01, 0.10)
      sigma_r = clip(0.02 + 0.03 * prec_star - 0.01 * hitter.E, 0.01, 0.10)

      # --- Estrategia: varianza ---
      sigma_p *= self._sm("sigma_pot_mult")
      sigma_r *= self._sm("sigma_prec_mult")

      pot_out = clip(np.random.normal(pot_star, sigma_p), 0.10, 0.95)
      prec_out = clip(np.random.normal(prec_star, sigma_r), 0.10, 0.97)

      # === Momentum ===
      m = hitter.Momentum / 100
      momentum_factor = 1.0 + 0.10 * m
      pot_out *= momentum_factor
      prec_out *= momentum_factor

      # === Clutch (calculado una vez) ===
      clutch_boost = 1.0
      if self.clutch:
          k = self.hitter.K
          clutch_boost = 1.0 + (k - 0.5) * 0.20  # ±10 %

      # Aplicar clutch a precision
      prec_out *= clutch_boost

      # === Estrategia: pot/prec ===
      pot_out *= self._sm("pot_mult")
      prec_out *= self._sm("prec_mult")
      prec_out = clip(prec_out, 0.10, 0.97)

      # === Probabilidad de meter la bola ===
      Q = 0.6 * hitter.RET + 0.4 * hitter.C
      Q_adj = Q - 0.5 * (shotQ_in - 0.5)
      p_in = clip(0.65 + 0.3 * (Q_adj - 0.5), 0.05, 0.99)

      eps = np.random.normal(0, 0.05 * (1 - hitter.C))
      p_final = clip(p_in + eps, 0.02, 0.99)
      p_final *= (1.0 + 0.10 * m)
      p_final *= clutch_boost
      p_final *= self._sm("p_in_mult")
      p_final = clip(p_final, 0.02, 0.99)

      in_flag = rand() < p_final

      self.feed.append(
          f"{hitter.name} golpea ({side_name}){' [CLUTCH]' if self.clutch else ''} → "
          f"Pot={pot_out:.2f}, Prec={prec_out:.2f}, p_in={p_final:.2f} → "
          f"{'DENTRO' if in_flag else 'FUERA'}"
      )

      if not in_flag:
          return None, {"side": side_name, "pot": pot_out, "prec": prec_out,
                        "p_in": p_final, "in": False}

      ball = Ball(pot=pot_out, prec=prec_out, side=side_name, by=RESTADOR)
      return ball, {"side": side_name, "pot": pot_out, "prec": prec_out,
                    "p_in": p_final, "in": True}


# ============================================================
# Clase RallyShot (Peloteo)
# ============================================================

class RallyShot(Shot):
    """
    Rally (peloteo) con las fórmulas EXACTAS acordadas:
      - Probabilidad de alcanzar la bola:
        pr = clip(0.72 + 0.30*(MOV - 0.70) + 0.20*(E - 0.70) - 0.55*(shotQ - 0.60), 0.02, 0.98)
      - Potencia y precisión base del golpe:
        pot_base  = 0.45*F + 0.25*E + 0.20*side + 0.10*C
        prec_base = 0.40*C + 0.30*side + 0.20*MOV + 0.10*E
      - Ajuste según calidad del golpe recibido:
        pot*  = pot_base  + 0.18*(0.50 - shotQ_in)
        prec* = prec_base + 0.22*(0.60 - shotQ_in)
      - Probabilidad de meter la bola:
        p_in = clip(0.65 + 0.3*(Q_adj - 0.5), 0.05, 0.99)
        con Q_adj = (0.6*A + 0.4*C) - 0.5*(shotQ_in - 0.5)
      - Ruido aleatorio dependiente de la consistencia y estamina:
        desv_p = 0.03 + 0.04*pot* - 0.02*E
        desv_r = 0.02 + 0.03*prec* - 0.01*E
    """

    def attempt_reach(self, incoming: Ball) -> Tuple[bool, float]:
        """Evalúa si el jugador logra alcanzar la bola durante el peloteo."""
        shotQ = incoming.shotQ
        mov = self.receiver.MOV
        est = self.receiver.E
        who = self.hitter

        pr = clip(
            0.72 + 0.30 * (mov - 0.70) + 0.20 * (est - 0.70) - 0.55 * (shotQ - 0.60),
            0.02, 0.98
        )

        # --- Momentum mejora un poco la capacidad de alcanzar la bola ---
        m = self.receiver.Momentum / 100
        pr *= (1.0 + 0.05 * m)

        # --- Estrategia: reach_mult ---
        pr *= self._sm("reach_mult")
        pr = clip(pr, 0.02, 0.98)

        ok = rand() < pr

        self.feed.append(
            f"   {who.name} → prob. alcanzar bola={pr:.2f} (shotQ_in={shotQ:.2f}) → {'ALCANZADO' if ok else 'NO LLEGA'}"
        )
        return ok, pr

    def produce_ball(self, incoming: Ball) -> Tuple[Optional[Ball], Dict]:
      """Genera la bola devuelta durante el peloteo."""
      hitter = self.hitter
      side_name, side = hitter.pick_side()

      pot_base  = 0.45 * hitter.F + 0.25 * hitter.E + 0.20 * side + 0.10 * hitter.C
      prec_base = 0.40 * hitter.C + 0.30 * side + 0.20 * hitter.MOV + 0.10 * hitter.E

      shotQ_in = incoming.shotQ
      pot_star  = clip(pot_base  + 0.18 * (0.50 - shotQ_in), 0.15, 0.75)
      prec_star = clip(prec_base + 0.22 * (0.60 - shotQ_in), 0.20, 0.92)

      sigma_p = clip(0.03 + 0.04 * pot_star - 0.02 * hitter.E, 0.01, 0.10)
      sigma_r = clip(0.02 + 0.03 * prec_star - 0.01 * hitter.E, 0.01, 0.10)

      # --- Estrategia: varianza ---
      sigma_p *= self._sm("sigma_pot_mult")
      sigma_r *= self._sm("sigma_prec_mult")

      pot_out  = clip(np.random.normal(pot_star, sigma_p), 0.10, 0.95)
      prec_out = clip(np.random.normal(prec_star, sigma_r), 0.10, 0.97)

      # === Momentum ===
      m = hitter.Momentum / 100
      momentum_factor = 1.0 + 0.15 * m
      pot_out *= momentum_factor
      prec_out *= momentum_factor

      # === Clutch (una sola vez) ===
      clutch_boost = 1.0
      if self.clutch:
          k = self.hitter.K
          clutch_boost = 1.0 + (k - 0.5) * 0.20  # ±10 %

      # Aplicar clutch a precision
      prec_out *= clutch_boost

      # === Estrategia: pot/prec ===
      pot_out *= self._sm("pot_mult")
      prec_out *= self._sm("prec_mult")
      prec_out = clip(prec_out, 0.10, 0.97)

      # === Probabilidad final ===
      A = side
      Q = 0.6 * A + 0.4 * hitter.C
      Q_adj = Q - 0.5 * (shotQ_in - 0.5)
      p_in = clip(0.65 + 0.3 * (Q_adj - 0.5), 0.05, 0.99)
      eps = np.random.normal(0, 0.05 * (1 - hitter.C))
      p_final = clip(p_in + eps, 0.02, 0.99)

      p_final *= (1.0 + 0.10 * m)
      p_final *= clutch_boost
      p_final *= self._sm("p_in_mult")
      p_final = clip(p_final, 0.02, 0.99)

      in_flag = rand() < p_final

      self.feed.append(
          f"{hitter.name} golpea ({side_name}){' [CLUTCH]' if self.clutch else ''} → "
          f"Pot={pot_out:.2f}, Prec={prec_out:.2f}, p_in={p_final:.2f} → "
          f"{'DENTRO' if in_flag else 'FUERA'}"
      )

      if not in_flag:
          return None, {"side": side_name, "pot": pot_out, "prec": prec_out,
                        "p_in": p_final, "in": False}

      ball = Ball(pot=pot_out, prec=prec_out, side=side_name, by=hitter.name)
      return ball, {"side": side_name, "pot": pot_out, "prec": prec_out,
                    "p_in": p_final, "in": True}
