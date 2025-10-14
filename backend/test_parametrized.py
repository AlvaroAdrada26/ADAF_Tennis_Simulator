# backend/test_parametrized.py
"""
Simulación de liga completa del ADAF Tennis Simulator (versión visual y corregida).
Cada jugador se enfrenta a todos los demás, mostrando resultados
y un ranking final tabulado con estadísticas coherentes.
"""

import itertools
from backend.simulator.api import run_match


# ============================================================
# Colores y estilos para consola
# ============================================================

class Color:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


# ============================================================
# Datos de jugadores
# ============================================================

PLAYERS = {
    "Alcaraz": dict(
        name="Alcaraz", Primer_Saque=82, Segundo_Saque=80,
        Fisico=88, Estamina=90, Consistencia=85,
        Clutch=88, Momentum=0, Derecha=89, Reves=86,
        Resto=84, Movilidad=90,
    ),
    "Sinner": dict(
        name="Sinner", Primer_Saque=85, Segundo_Saque=82,
        Fisico=87, Estamina=88, Consistencia=86,
        Clutch=85, Momentum=0, Derecha=88, Reves=90,
        Resto=83, Movilidad=88,
    ),
    "Nadal": dict(
        name="Nadal", Primer_Saque=78, Segundo_Saque=75,
        Fisico=94, Estamina=97, Consistencia=90,
        Clutch=95, Momentum=0, Derecha=94, Reves=82,
        Resto=90, Movilidad=88,
    ),
    "Djokovic": dict(
        name="Djokovic", Primer_Saque=84, Segundo_Saque=81,
        Fisico=89, Estamina=95, Consistencia=92,
        Clutch=96, Momentum=0, Derecha=88, Reves=94,
        Resto=91, Movilidad=90,
    ),
    "Federer": dict(
        name="Federer", Primer_Saque=86, Segundo_Saque=83,
        Fisico=85, Estamina=88, Consistencia=89,
        Clutch=94, Momentum=0, Derecha=92, Reves=90,
        Resto=88, Movilidad=86,
    ),
    "Amateur": dict(
        name="Amateur", Primer_Saque=55, Segundo_Saque=50,
        Fisico=60, Estamina=65, Consistencia=55,
        Clutch=50, Momentum=0, Derecha=58, Reves=52,
        Resto=50, Movilidad=58,
    ),
}


# ============================================================
# Simulación de liga completa
# ============================================================

def simulate_league():
    config = {"best_of": 3, "tiebreak": True, "seed": None}
    results = {
        name: {
            "wins": 0, "losses": 0,
            "games_won": 0, "games_lost": 0,
            "sets_won": 0, "sets_lost": 0,
        }
        for name in PLAYERS
    }

    print(f"\n{Color.BOLD}{Color.CYAN}================= LIGA ADAF TENNIS SIMULATOR ================={Color.RESET}\n")

    # Todos contra todos
    for p1_name, p2_name in itertools.combinations(PLAYERS.keys(), 2):
        p1, p2 = PLAYERS[p1_name], PLAYERS[p2_name]
        result = run_match(p1, p2, config)

        winner = result["winner"]
        loser = p1_name if winner == p2_name else p2_name
        sets = result["set_scores"]

        # === Actualizar estadísticas ===
        results[winner]["wins"] += 1
        results[loser]["losses"] += 1

        # Sets totales
        results[p1_name]["sets_won"]  += result["sets_won"]["P1"]
        results[p1_name]["sets_lost"] += result["sets_won"]["P2"]
        results[p2_name]["sets_won"]  += result["sets_won"]["P2"]
        results[p2_name]["sets_lost"] += result["sets_won"]["P1"]

        # Juegos totales
        for g1, g2 in result["set_scores"]:
            results[p1_name]["games_won"]  += g1
            results[p1_name]["games_lost"] += g2
            results[p2_name]["games_won"]  += g2
            results[p2_name]["games_lost"] += g1

        # === Mostrar resultado visual ===
        print(f"{Color.YELLOW}{p1_name}{Color.RESET} vs {Color.YELLOW}{p2_name}{Color.RESET}")
        print(f"  → Ganador: {Color.GREEN if winner != 'Amateur' else Color.RED}{winner}{Color.RESET}")
        print(f"  → Sets: {sets}")
        print(f"  → Marcador total: {result['sets_won']}")
        print(f"  ------------------------------------------------------{Color.RESET}")

    # ============================================================
    # Ranking final
    # ============================================================
    print(f"\n{Color.BOLD}{Color.CYAN}================= RANKING FINAL ================={Color.RESET}\n")

    ranking = sorted(
        results.items(),
        key=lambda kv: (kv[1]["wins"], kv[1]["games_won"] - kv[1]["games_lost"]),
        reverse=True,
    )

    # Encabezado tabla
    print(f"{Color.BOLD}{'Pos':<4} {'Jugador':<12} {'W':>3} {'L':>3} "
          f"{'%Win':>7} {'Games+':>7} {'Games-':>7} {'Sets+':>7} {'Sets-':>7}{Color.RESET}")
    print(f"{Color.CYAN}{'-'*68}{Color.RESET}")

    # Filas del ranking
    for i, (name, stats) in enumerate(ranking, start=1):
        total = stats["wins"] + stats["losses"]
        pct = stats["wins"] / total * 100 if total > 0 else 0
        color = Color.GREEN if i == 1 else (Color.YELLOW if i <= 3 else Color.RED)
        print(
            f"{color}{i:<4} {name:<12} {stats['wins']:>3} {stats['losses']:>3} "
            f"{pct:>6.1f}% {stats['games_won']:>7} {stats['games_lost']:>7} "
            f"{stats['sets_won']:>7} {stats['sets_lost']:>7}{Color.RESET}"
        )

    print(f"\n{Color.CYAN}{'='*68}{Color.RESET}\n")


# ============================================================
# Ejecución directa
# ============================================================

if __name__ == "__main__":
    simulate_league()
