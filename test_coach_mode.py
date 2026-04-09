"""
Test exhaustivo del Modo Entrenador.

Ejecuta partidos completos directamente con el motor de simulación
(sin servidor HTTP) para verificar:
  1. Todos los partidos terminan correctamente
  2. El marcador es coherente (sets, games, puntos)
  3. La estamina baja durante el partido
  4. El momentum se mueve de forma razonable
  5. Las estrategias generan diferencias estadísticas
  6. Los break points y clutch points se detectan bien
  7. Los tiebreaks funcionan
"""
import sys, os, copy, statistics, time
from collections import Counter

# Asegurar imports
sys.path.insert(0, os.path.dirname(__file__))

from backend.simulator.models import Player
from backend.simulator.point import PointSimulator
from backend.simulator.scorekeeper import MatchScorekeeper
from backend.simulator.strategy import get_modifiers, VALID_STRATEGIES
from backend.simulator.utils import SACADOR, RESTADOR


# ─── Jugadores de prueba ──────────────────────────────────
def make_player(name, id_, overall=75):
    """Crea un jugador con todos los atributos iguales al overall dado."""
    return Player(
        name=name, id=id_,
        Primer_Saque=overall, Segundo_Saque=overall - 5,
        Fisico=overall, Estamina=100.0,
        Consistencia=overall, Clutch=overall,
        Momentum=0.0,
        Derecha=overall, Reves=overall - 5,
        Resto=overall, Movilidad=overall,
    )

def make_player_strong_serve(name, id_):
    return Player(
        name=name, id=id_,
        Primer_Saque=92, Segundo_Saque=85,
        Fisico=70, Estamina=100.0,
        Consistencia=65, Clutch=75,
        Momentum=0.0,
        Derecha=78, Reves=70,
        Resto=60, Movilidad=68,
    )

def make_player_baseline(name, id_):
    return Player(
        name=name, id=id_,
        Primer_Saque=68, Segundo_Saque=65,
        Fisico=85, Estamina=100.0,
        Consistencia=88, Clutch=70,
        Momentum=0.0,
        Derecha=82, Reves=80,
        Resto=80, Movilidad=85,
    )

# ─── Simular un partido completo ─────────────────────────
def simulate_full_match(p1_template, p2_template, strategy_p1=None,
                        best_of=3, tiebreak=True, max_points=800):
    """
    Simula un partido completo punto a punto.
    Devuelve dict con estadísticas del partido.
    """
    p1 = copy.deepcopy(p1_template)
    p2 = copy.deepcopy(p2_template)
    p1.reset_dynamic_state()
    p2.reset_dynamic_state()

    sk = MatchScorekeeper(p1, p2, best_of=best_of, tiebreak=tiebreak)

    total_points = 0
    total_rally_shots = 0
    p1_points_won = 0
    p2_points_won = 0
    break_points_faced = 0
    break_points_converted = 0
    clutch_points = 0
    tiebreaks_played = 0
    min_stamina_p1 = 100.0
    min_stamina_p2 = 100.0
    errors = []

    coached_mods = get_modifiers(strategy_p1)

    while not sk.match_finished:
        total_points += 1
        if total_points > max_points:
            errors.append(f"PARTIDO NO TERMINA tras {max_points} puntos")
            break

        server_id, returner_id = sk.get_server_returner()
        server_obj = sk.get_player(server_id)
        returner_obj = sk.get_player(returner_id)

        # Estrategia sólo para P1
        if coached_mods:
            if server_id == "P1":
                s_strat, r_strat = coached_mods, None
            else:
                s_strat, r_strat = None, coached_mods
        else:
            s_strat, r_strat = None, None

        is_bp = sk.is_break_point()
        is_clutch = sk.is_clutch_point()
        if is_bp:
            break_points_faced += 1
        if is_clutch:
            clutch_points += 1
        if sk.is_tiebreak and total_points > 1:
            pass  # contaremos tiebreaks al final

        tags = {SACADOR: server_id, RESTADOR: returner_id}
        ps = PointSimulator(
            server_obj, returner_obj,
            clutch=is_clutch,
            tags=tags,
            server_strategy=s_strat,
            returner_strategy=r_strat,
        )
        result = ps.simulate(verbose=False)
        rally_shots = result.stats.get("rally_shots", 0)
        total_rally_shots += rally_shots

        events = sk.register_point(result.winner, rally_shots)

        if events["winner_id"] == "P1":
            p1_points_won += 1
            if is_bp and server_id == "P2":
                break_points_converted += 1
        else:
            p2_points_won += 1
            if is_bp and server_id == "P1":
                break_points_converted += 1

        min_stamina_p1 = min(min_stamina_p1, p1.Estamina)
        min_stamina_p2 = min(min_stamina_p2, p2.Estamina)

    # Contar tiebreaks en set_scores
    for g1, g2 in sk.set_scores:
        if g1 == 7 or g2 == 7:
            tiebreaks_played += 1

    # Validaciones
    if sk.match_finished:
        winner_sets = sk.sets[sk.winner]
        loser = "P2" if sk.winner == "P1" else "P1"
        loser_sets = sk.sets[loser]
        if winner_sets < sk.sets_needed:
            errors.append(f"Ganador {sk.winner} sólo tiene {winner_sets} sets (necesita {sk.sets_needed})")
        if loser_sets >= sk.sets_needed:
            errors.append(f"Perdedor {loser} tiene {loser_sets} sets >= {sk.sets_needed}")
        if len(sk.set_scores) != winner_sets + loser_sets:
            errors.append(f"set_scores ({len(sk.set_scores)}) != total sets ({winner_sets + loser_sets})")
        for i, (g1, g2) in enumerate(sk.set_scores):
            winner_g = max(g1, g2)
            loser_g = min(g1, g2)
            if tiebreak:
                if winner_g == 7 and loser_g == 6:
                    pass  # tiebreak set, ok
                elif winner_g >= 6 and winner_g - loser_g >= 2:
                    pass  # normal set
                else:
                    errors.append(f"Set {i+1} inválido: {g1}-{g2}")
            else:
                if winner_g >= 6 and winner_g - loser_g >= 2:
                    pass
                else:
                    errors.append(f"Set {i+1} inválido (sin TB): {g1}-{g2}")

    return {
        "winner": sk.winner,
        "set_scores": sk.set_scores,
        "total_points": total_points,
        "p1_points": p1_points_won,
        "p2_points": p2_points_won,
        "avg_rally": total_rally_shots / max(total_points, 1),
        "break_points_faced": break_points_faced,
        "break_points_converted": break_points_converted,
        "clutch_points": clutch_points,
        "tiebreaks": tiebreaks_played,
        "min_stamina_p1": min_stamina_p1,
        "min_stamina_p2": min_stamina_p2,
        "final_stamina_p1": p1.Estamina,
        "final_stamina_p2": p2.Estamina,
        "final_momentum_p1": p1.Momentum,
        "final_momentum_p2": p2.Momentum,
        "errors": errors,
        "finished": sk.match_finished,
        "strategy": strategy_p1,
    }


# ─── Batch runner ─────────────────────────────────────────
def run_batch(label, p1_template, p2_template, strategy=None,
              n=50, best_of=3, tiebreak=True):
    print(f"\n{'='*70}")
    print(f"  {label}  (n={n}, best_of={best_of}, strategy_P1={strategy})")
    print(f"{'='*70}")

    results = []
    all_errors = []
    t0 = time.time()

    for i in range(n):
        res = simulate_full_match(
            p1_template, p2_template,
            strategy_p1=strategy, best_of=best_of, tiebreak=tiebreak,
        )
        results.append(res)
        if res["errors"]:
            all_errors.extend([(i, e) for e in res["errors"]])

    elapsed = time.time() - t0

    # Aggregate stats
    wins_p1 = sum(1 for r in results if r["winner"] == "P1")
    wins_p2 = sum(1 for r in results if r["winner"] == "P2")
    finished = sum(1 for r in results if r["finished"])
    not_finished = n - finished

    points_list = [r["total_points"] for r in results]
    rally_list = [r["avg_rally"] for r in results]
    bp_faced = [r["break_points_faced"] for r in results]
    bp_conv = [r["break_points_converted"] for r in results]
    clutch_list = [r["clutch_points"] for r in results]
    tb_list = [r["tiebreaks"] for r in results]
    min_stam_p1 = [r["min_stamina_p1"] for r in results]
    min_stam_p2 = [r["min_stamina_p2"] for r in results]
    final_stam_p1 = [r["final_stamina_p1"] for r in results]
    final_stam_p2 = [r["final_stamina_p2"] for r in results]

    def stat_line(label, data):
        if not data:
            return f"  {label}: N/A"
        return (f"  {label}: mean={statistics.mean(data):.2f}, "
                f"median={statistics.median(data):.2f}, "
                f"min={min(data):.2f}, max={max(data):.2f}, "
                f"stdev={statistics.stdev(data):.2f}" if len(data) > 1
                else f"  {label}: {data[0]:.2f}")

    print(f"\n  Tiempo: {elapsed:.2f}s ({elapsed/n*1000:.0f}ms/partido)")
    print(f"  Terminados: {finished}/{n}" + (f" *** {not_finished} NO TERMINARON ***" if not_finished else ""))
    print(f"  Victorias P1: {wins_p1} ({wins_p1/n*100:.1f}%)  |  P2: {wins_p2} ({wins_p2/n*100:.1f}%)")
    print()
    print(stat_line("Total puntos", points_list))
    print(stat_line("Rally medio", rally_list))
    print(stat_line("Break points", bp_faced))
    print(stat_line("BP convertidos", bp_conv))
    print(stat_line("Clutch points", clutch_list))
    print(stat_line("Tiebreaks", tb_list))
    print()
    print(stat_line("Min estam P1", min_stam_p1))
    print(stat_line("Min estam P2", min_stam_p2))
    print(stat_line("Final estam P1", final_stam_p1))
    print(stat_line("Final estam P2", final_stam_p2))

    # Set score distribution
    set_score_counter = Counter()
    for r in results:
        for sc in r["set_scores"]:
            set_score_counter[sc] += 1
    print(f"\n  Distribución de marcadores de set:")
    for sc, count in sorted(set_score_counter.items(), key=lambda x: -x[1]):
        print(f"    {sc[0]}-{sc[1]}: {count} ({count/sum(set_score_counter.values())*100:.1f}%)")

    # Match length distribution
    sets_played = Counter()
    for r in results:
        sets_played[len(r["set_scores"])] += 1
    print(f"\n  Largo del partido (sets):")
    for nsets, count in sorted(sets_played.items()):
        print(f"    {nsets} sets: {count} ({count/n*100:.1f}%)")

    if all_errors:
        print(f"\n  *** ERRORES ({len(all_errors)}) ***")
        for idx, err in all_errors[:20]:
            print(f"    Partido {idx}: {err}")
    else:
        print(f"\n  Sin errores")

    return {
        "wins_p1": wins_p1,
        "wins_p2": wins_p2,
        "mean_points": statistics.mean(points_list),
        "errors": all_errors,
        "results": results,
    }


# ─── Main ─────────────────────────────────────────────────
if __name__ == "__main__":
    N = 100

    p_equal_1 = make_player("Jugador A", "P1", overall=75)
    p_equal_2 = make_player("Jugador B", "P2", overall=75)

    p_server = make_player_strong_serve("Big Server", "P1")
    p_base = make_player_baseline("Baseliner", "P2")

    p_strong = make_player("Fuerte", "P1", overall=88)
    p_weak = make_player("Débil", "P2", overall=62)

    print("\n" + "#"*70)
    print("#  TEST MODO ENTRENADOR — Simulación exhaustiva")
    print("#"*70)

    # ── Test 1: Jugadores iguales, sin estrategia ─────────
    r1 = run_batch("Test 1: Iguales, sin estrategia", p_equal_1, p_equal_2, n=N)

    # ── Test 2: Jugadores iguales, P1 agresivo ────────────
    r2 = run_batch("Test 2: Iguales, P1 agresivo", p_equal_1, p_equal_2,
                   strategy="aggressive", n=N)

    # ── Test 3: Jugadores iguales, P1 defensivo ───────────
    r3 = run_batch("Test 3: Iguales, P1 defensivo", p_equal_1, p_equal_2,
                   strategy="defensive", n=N)

    # ── Test 4: Server vs Baseliner, sin estrategia ───────
    r4 = run_batch("Test 4: Server vs Baseliner", p_server, p_base, n=N)

    # ── Test 5: Fuerte vs Débil ───────────────────────────
    r5 = run_batch("Test 5: Fuerte (88) vs Débil (62)", p_strong, p_weak, n=N)

    # ── Test 6: Best of 5 ─────────────────────────────────
    r6 = run_batch("Test 6: Bo5, iguales", p_equal_1, p_equal_2,
                   best_of=5, n=N)

    # ── Test 7: Sin tiebreak ──────────────────────────────
    r7 = run_batch("Test 7: Sin tiebreak", p_equal_1, p_equal_2,
                   tiebreak=False, n=N//2)

    # ── Resumen final ─────────────────────────────────────
    print("\n\n" + "#"*70)
    print("#  RESUMEN FINAL")
    print("#"*70)

    all_batches = [
        ("T1 Neutral", r1),
        ("T2 Agresivo", r2),
        ("T3 Defensivo", r3),
        ("T4 Srv vs Base", r4),
        ("T5 Fuerte vs Débil", r5),
        ("T6 Bo5", r6),
        ("T7 Sin TB", r7),
    ]

    total_errors = 0
    print(f"\n  {'Test':<20} {'P1 wins':>8} {'P2 wins':>8} {'Avg pts':>8} {'Errores':>8}")
    print(f"  {'-'*56}")
    for label, batch in all_batches:
        print(f"  {label:<20} {batch['wins_p1']:>7}  {batch['wins_p2']:>7}  "
              f"{batch['mean_points']:>7.1f}  {len(batch['errors']):>7}")
        total_errors += len(batch["errors"])

    # ── Comparación de estrategias ────────────────────────
    print(f"\n  Efecto de la estrategia (jugadores iguales):")
    print(f"    Neutral:   P1 gana {r1['wins_p1']}/{N} = {r1['wins_p1']/N*100:.1f}%")
    print(f"    Agresivo:  P1 gana {r2['wins_p1']}/{N} = {r2['wins_p1']/N*100:.1f}%")
    print(f"    Defensivo: P1 gana {r3['wins_p1']}/{N} = {r3['wins_p1']/N*100:.1f}%")

    # ── Sanity checks ─────────────────────────────────────
    print(f"\n  Sanity checks:")
    ok = True

    # El fuerte debería ganar más
    if r5["wins_p1"] < r5["wins_p2"]:
        print(f"    [WARN] El jugador fuerte (88 vs 62) perdió más de lo que ganó: {r5['wins_p1']} vs {r5['wins_p2']}")
        ok = False
    else:
        print(f"    [OK] Fuerte gana más que débil ({r5['wins_p1']} vs {r5['wins_p2']})")

    # Bo5 debería tener más puntos que Bo3
    if r6["mean_points"] <= r1["mean_points"]:
        print(f"    [WARN] Bo5 ({r6['mean_points']:.0f} pts) no tiene más puntos que Bo3 ({r1['mean_points']:.0f} pts)")
        ok = False
    else:
        print(f"    [OK] Bo5 ({r6['mean_points']:.0f} pts) > Bo3 ({r1['mean_points']:.0f} pts)")

    # Jugadores iguales: winrate debería estar en ~35%-65%
    ratio = r1["wins_p1"] / N
    if 0.30 <= ratio <= 0.70:
        print(f"    [OK] Jugadores iguales, P1 gana {ratio*100:.0f}% (rango 30-70%)")
    else:
        print(f"    [WARN] Jugadores iguales, P1 gana {ratio*100:.0f}% (fuera de 30-70%)")
        ok = False

    # Sin errores
    if total_errors == 0:
        print(f"    [OK] 0 errores en todos los tests")
    else:
        print(f"    [FAIL] {total_errors} errores encontrados")
        ok = False

    if ok:
        print(f"\n  *** TODOS LOS TESTS PASARON ***\n")
    else:
        print(f"\n  *** ALGUNOS WARNINGS — revisar arriba ***\n")
