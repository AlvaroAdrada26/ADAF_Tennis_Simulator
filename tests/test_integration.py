"""
Pruebas de integración del ADAF Tennis Simulator.
Verifican el flujo completo de una simulación de extremo a extremo.
"""

import pytest
from backend.simulator.api import run_match


# -- Datos de jugadores compartidos --

P1 = dict(
    name="Alcaraz", id="P1",
    Primer_Saque=82, Segundo_Saque=78, Fisico=88, Estamina=90,
    Consistencia=85, Clutch=88, Momentum=0,
    Derecha=89, Reves=86, Resto=84, Movilidad=90,
)

P2 = dict(
    name="Sinner", id="P2",
    Primer_Saque=85, Segundo_Saque=80, Fisico=87, Estamina=88,
    Consistencia=86, Clutch=85, Momentum=0,
    Derecha=88, Reves=90, Resto=83, Movilidad=88,
)

CFG_BO3 = {"best_of": 3, "tiebreak": True, "seed": 42}


# -- Estructura del resultado --

def test_run_match_devuelve_campos_obligatorios():
    result = run_match(P1, P2, CFG_BO3)
    for campo in ("winner_name", "winner_id", "set_scores", "sets_won", "timeline"):
        assert campo in result, f"Falta el campo '{campo}' en el resultado"

def test_run_match_ganador_es_uno_de_los_dos():
    result = run_match(P1, P2, CFG_BO3)
    assert result["winner_id"] in {"P1", "P2"}

def test_run_match_timeline_no_vacio():
    result = run_match(P1, P2, CFG_BO3)
    assert len(result["timeline"]) > 0

def test_run_match_sets_ganados_coherentes():
    """El ganador debe haber ganado más sets que el perdedor."""
    result = run_match(P1, P2, CFG_BO3)
    sw = result["sets_won"]
    assert max(sw["P1"], sw["P2"]) == 2  # best_of=3 = necesita 2 sets

def test_run_match_set_scores_formato():
    """Cada elemento de set_scores debe ser una tupla/lista de dos enteros."""
    result = run_match(P1, P2, CFG_BO3)
    for score in result["set_scores"]:
        assert len(score) == 2
        assert all(isinstance(n, int) for n in score)


# -- Reproducibilidad --

def test_misma_semilla_mismo_resultado():
    r1 = run_match(P1, P2, {"best_of": 3, "tiebreak": True, "seed": 7})
    r2 = run_match(P1, P2, {"best_of": 3, "tiebreak": True, "seed": 7})
    assert r1["winner_id"] == r2["winner_id"]
    assert r1["set_scores"] == r2["set_scores"]

def test_distinta_semilla_puede_variar():
    """Con semillas distintas el resultado puede cambiar (no debe ser siempre igual)."""
    resultados = set()
    for seed in range(20):
        r = run_match(P1, P2, {"best_of": 3, "tiebreak": True, "seed": seed})
        resultados.add(r["winner_id"])
    # En 20 partidos debe ganar cada jugador al menos una vez
    assert len(resultados) == 2


# -- Formatos de partido --

def test_best_of_5_necesita_3_sets():
    result = run_match(P1, P2, {"best_of": 5, "tiebreak": True, "seed": 42})
    sw = result["sets_won"]
    assert max(sw["P1"], sw["P2"]) == 3

def test_best_of_1_termina_en_un_set():
    result = run_match(P1, P2, {"best_of": 1, "tiebreak": True, "seed": 42})
    assert len(result["set_scores"]) == 1


# -- Jugador debil pierde mas veces --

def test_jugador_fuerte_gana_mayoria():
    """Un jugador con todos los atributos muy superiores debe ganar la mayoría."""
    fuerte = dict(
        name="Pro", id="P1",
        Primer_Saque=99, Segundo_Saque=99, Fisico=99, Estamina=99,
        Consistencia=99, Clutch=99, Momentum=0,
        Derecha=99, Reves=99, Resto=99, Movilidad=99,
    )
    debil = dict(
        name="Aficionado", id="P2",
        Primer_Saque=30, Segundo_Saque=30, Fisico=30, Estamina=30,
        Consistencia=30, Clutch=30, Momentum=0,
        Derecha=30, Reves=30, Resto=30, Movilidad=30,
    )
    victorias_fuerte = sum(
        1 for seed in range(10)
        if run_match(fuerte, debil, {"best_of": 3, "tiebreak": True, "seed": seed})["winner_id"] == "P1"
    )
    assert victorias_fuerte >= 8  # debe ganar al menos 8 de 10
