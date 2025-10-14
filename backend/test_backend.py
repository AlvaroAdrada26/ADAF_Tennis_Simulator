"""
Test funcional extendido del simulador ADAF Tennis Simulator.
"""

from backend.simulator.api import run_match


def test_run_match_basic():
    # --- Jugadores de prueba (simples) ---
    player1 = {
        "name": "Alcaraz",
        "Primer_Saque": 82,
        "Segundo_Saque": 80,
        "Fisico": 88,
        "Estamina": 90,
        "Consistencia": 85,
        "Clutch": 88,
        "Momentum": 0,
        "Derecha": 89,
        "Reves": 86,
        "Resto": 84,
        "Movilidad": 90,
    }

    player2 = {
        "name": "Sinner",
        "Primer_Saque": 85,
        "Segundo_Saque": 82,
        "Fisico": 87,
        "Estamina": 88,
        "Consistencia": 86,
        "Clutch": 85,
        "Momentum": 0,
        "Derecha": 88,
        "Reves": 90,
        "Resto": 83,
        "Movilidad": 88,
    }

    # --- Configuración reducida para test rápido ---
    config = {
        "best_of": 3,
        "tiebreak": True,
        "seed": 42,  # reproducible
    }

    # --- Ejecutar simulación ---
    result = run_match(player1, player2, config)

    # --- Validaciones básicas ---
    assert isinstance(result, dict)
    assert "winner" in result
    assert "set_scores" in result
    assert "sets_won" in result

    # --- Impresión de resumen ---
    print("\n================= RESULTADO DEL TEST =================")
    print(f"Ganador: {result['winner']}")
    print(f"Sets ganados: {result['sets_won']}")
    print(f"Marcadores por set: {result['set_scores']}")
    print(f"Formato best_of: {result['best_of']}, Tiebreak: {result['tiebreak']}")
    if "summary" in result:
        print(f"Resumen: {result['summary']}")

    # --- Reproducibilidad: repetir con la misma semilla ---
    same_seed = run_match(player1, player2, config)
    different_seed = run_match(player1, player2, {**config, "seed": 99})

    print("\n--- Comprobación de reproducibilidad ---")
    if same_seed == result:
        print("Mismo resultado con la misma semilla (reproducible).")
    else:
        print("Diferencia inesperada con la misma semilla.")
    if different_seed != result:
        print("Resultado distinto con semilla diferente (aleatoriedad correcta).")
    else:
        print("Mismo resultado con semilla distinta (revisar aleatoriedad).")

    print("\nSimulación ejecutada correctamente.\n")


if __name__ == "__main__":
    test_run_match_basic()
