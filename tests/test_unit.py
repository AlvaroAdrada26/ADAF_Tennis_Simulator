"""
Pruebas unitarias del ADAF Tennis Simulator.
Comprueban componentes aislados: utilidades, modelos y clases de puntuación.
"""

import pytest
from backend.simulator.utils import clip, seed_all, SACADOR, RESTADOR
from backend.simulator.models import Player, Config
from backend.simulator.scoring import TennisGame, TennisSet


# ─── Fixture: jugadores de prueba ────────────────────────────────────────────

@pytest.fixture
def player_a():
    return Player(
        name="Alcaraz", id="P1",
        Primer_Saque=82, Segundo_Saque=78, Fisico=88, Estamina=90,
        Consistencia=85, Clutch=88, Momentum=0,
        Derecha=89, Reves=86, Resto=84, Movilidad=90,
    )


@pytest.fixture
def player_b():
    return Player(
        name="Sinner", id="P2",
        Primer_Saque=85, Segundo_Saque=80, Fisico=87, Estamina=88,
        Consistencia=86, Clutch=85, Momentum=0,
        Derecha=88, Reves=90, Resto=83, Movilidad=88,
    )


# ─── Utilidades ──────────────────────────────────────────────────────────────

def test_clip_dentro_rango():
    assert clip(0.5, 0.0, 1.0) == 0.5

def test_clip_por_debajo():
    assert clip(-1.0, 0.0, 1.0) == 0.0

def test_clip_por_encima():
    assert clip(2.0, 0.0, 1.0) == 1.0


# ─── Modelo Player ───────────────────────────────────────────────────────────

def test_player_atributos_normalizados(player_a):
    """Las propiedades S1, S2, etc. deben devolver el valor dividido entre 100."""
    assert player_a.S1 == pytest.approx(0.82)
    assert player_a.S2 == pytest.approx(0.78)

def test_player_identidad(player_a):
    assert player_a.name == "Alcaraz"
    assert player_a.id == "P1"


# ─── Config ──────────────────────────────────────────────────────────────────

def test_config_defaults():
    cfg = Config()
    assert cfg.best_of == 3
    assert cfg.tiebreak is True
    assert cfg.seed is None

def test_config_personalizada():
    cfg = Config(best_of=5, tiebreak=False, seed=7)
    assert cfg.best_of == 5
    assert cfg.tiebreak is False
    assert cfg.seed == 7


# ─── Reproducibilidad ────────────────────────────────────────────────────────

def test_seed_produce_mismos_resultados(player_a, player_b):
    """Con la misma semilla, dos juegos deben tener el mismo ganador."""
    seed_all(42)
    game1 = TennisGame(player_a, player_b, player_a, player_b)
    winner1 = game1.play()

    seed_all(42)
    game2 = TennisGame(player_a, player_b, player_a, player_b)
    winner2 = game2.play()

    assert winner1 == winner2


# ─── TennisGame ──────────────────────────────────────────────────────────────

def test_tennis_game_produce_ganador(player_a, player_b):
    seed_all(0)
    game = TennisGame(player_a, player_b, player_a, player_b)
    winner = game.play()
    assert winner in {SACADOR, RESTADOR}

def test_tennis_game_feed_no_vacio(player_a, player_b):
    seed_all(0)
    game = TennisGame(player_a, player_b, player_a, player_b)
    game.play()
    assert len(game.feed) > 0


# ─── TennisSet ───────────────────────────────────────────────────────────────

def test_tennis_set_produce_ganador(player_a, player_b):
    seed_all(1)
    tset = TennisSet(player_a, player_b, tiebreak=True, set_no=1)
    winner, score, _ = tset.play()
    assert winner in {"P1", "P2"}

def test_tennis_set_marcador_valido(player_a, player_b):
    """El ganador debe tener al menos 6 juegos."""
    seed_all(1)
    tset = TennisSet(player_a, player_b, tiebreak=True, set_no=1)
    winner, score, _ = tset.play()
    assert max(score) >= 6
