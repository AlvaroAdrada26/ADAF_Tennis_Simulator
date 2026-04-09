"""
Funciones de agregación para el Modo Big Data.

Recibe una lista de resultados individuales de run_match() + extract_player_stats()
y produce estadísticas agregadas para N partidos.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


def aggregate_bigdata_stats(
    results: List[Dict[str, Any]],
    player1_name: str,
    player2_name: str,
    config_summary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Agrega estadísticas de N partidos simulados.

    Parameters
    ----------
    results : list[dict]
        Cada elemento es el resultado de ``run_match()`` con ``player_stats``
        ya inyectado (vía ``extract_player_stats``).
    player1_name, player2_name : str
        Nombres para display.
    config_summary : dict | None
        Resumen de la config (best_of, tiebreak, superficie) para metadata.

    Returns
    -------
    dict   Estructura completa de estadísticas Big Data.
    """
    n = len(results)
    if n == 0:
        return {"error": "No hay resultados para agregar"}

    # ── Contadores generales ──────────────────────────────────────────────
    wins = {"P1": 0, "P2": 0}
    sets_won = {"P1": 0, "P2": 0}
    score_distribution: Counter = Counter()  # "2-0", "2-1", etc.
    set_score_frequency: Counter = Counter()  # "6-4", "7-5", etc.
    total_points_all = 0
    min_points = float("inf")
    max_points = 0
    total_sets_all = 0

    # Stats keys from extract_player_stats
    STAT_KEYS = [
        "aces",
        "dobles_faltas",
        "primeros_saques_in",
        "primeros_saques_total",
        "puntos_ganados_1er_saque",
        "puntos_ganados_2do_saque",
        "winners",
        "errores_no_forzados",
        "puntos_ganados_resto",
        "total_puntos_ganados",
        "break_points_convertidos",
        "break_points_oportunidades",
    ]

    total_stats: Dict[str, Dict[str, int]] = {
        tag: {k: 0 for k in STAT_KEYS} for tag in ("P1", "P2")
    }

    # Rally distribution buckets
    rally_buckets = {"1": 0, "2": 0, "3-5": 0, "6-10": 0, "11+": 0}

    # Win rate progression (sample every 1% or 10 matches, whichever is larger)
    progression_step = max(10, n // 100)
    win_rate_progression: List[Dict[str, Any]] = []

    # ── Iterar sobre cada resultado ───────────────────────────────────────
    for i, r in enumerate(results):
        winner_id = r.get("winner_id", "P1")
        wins[winner_id] += 1

        # Sets won
        sw = r.get("sets_won", {})
        sets_won["P1"] += sw.get("P1", 0)
        sets_won["P2"] += sw.get("P2", 0)
        total_sets_all += sw.get("P1", 0) + sw.get("P2", 0)

        # Score distribution (e.g. "2-0", "1-2")
        s1, s2 = sw.get("P1", 0), sw.get("P2", 0)
        score_distribution[f"{s1}-{s2}"] += 1

        # Set score frequency (e.g. "6-4", "7-6")
        for a, b in r.get("set_scores", []):
            set_score_frequency[f"{a}-{b}"] += 1

        # Timeline stats
        timeline = r.get("timeline", [])
        n_points = len(timeline)
        total_points_all += n_points
        if n_points < min_points:
            min_points = n_points
        if n_points > max_points:
            max_points = n_points

        # Rally distribution
        for pt in timeline:
            stats = pt.get("stats") or {}
            rs = stats.get("rally_shots", 0)
            reason = pt.get("reason", "")
            # Total shots in point = serve(s) + return + rally
            # Approximate: ace/doble_falta = 1 shot, otherwise 2 + rally_shots
            if reason in ("ace", "doble_falta"):
                total_shots = 1
            elif reason in ("error_resto",):
                total_shots = 2
            else:
                total_shots = 2 + rs  # serve + return + rally

            if total_shots <= 1:
                rally_buckets["1"] += 1
            elif total_shots == 2:
                rally_buckets["2"] += 1
            elif total_shots <= 5:
                rally_buckets["3-5"] += 1
            elif total_shots <= 10:
                rally_buckets["6-10"] += 1
            else:
                rally_buckets["11+"] += 1

        # Player stats accumulation
        ps = r.get("player_stats", {})
        for tag in ("P1", "P2"):
            tag_stats = ps.get(tag, {})
            for k in STAT_KEYS:
                total_stats[tag][k] += tag_stats.get(k, 0)

        # Win rate progression
        if (i + 1) % progression_step == 0 or i == n - 1:
            p1_pct = round(wins["P1"] / (i + 1) * 100, 1)
            p2_pct = round(wins["P2"] / (i + 1) * 100, 1)
            win_rate_progression.append({
                "match": i + 1,
                "p1_pct": p1_pct,
                "p2_pct": p2_pct,
            })

    # ── Calcular promedios ────────────────────────────────────────────────
    avg_stats: Dict[str, Dict[str, float]] = {}
    for tag in ("P1", "P2"):
        avg = {}
        for k in STAT_KEYS:
            avg[k] = round(total_stats[tag][k] / n, 1)

        # Derived averages
        ps_in = avg["primeros_saques_in"]
        ps_total = avg["primeros_saques_total"]
        avg["primer_saque_pct"] = round(ps_in / ps_total * 100, 1) if ps_total > 0 else 0.0

        bp_conv = avg["break_points_convertidos"]
        bp_opp = avg["break_points_oportunidades"]
        avg["bp_conversion_pct"] = round(bp_conv / bp_opp * 100, 1) if bp_opp > 0 else 0.0

        avg_stats[tag] = avg

    # ── Construir respuesta ───────────────────────────────────────────────
    avg_points = round(total_points_all / n, 1) if n > 0 else 0
    avg_sets = round(total_sets_all / n, 2) if n > 0 else 0
    avg_duration_min = round(avg_points * 35 / 60) if avg_points > 0 else 0

    return {
        "meta": {
            "total_matches": n,
            "player1": player1_name,
            "player2": player2_name,
            "config": config_summary or {},
        },
        "win_rate": {
            "P1": {"wins": wins["P1"], "pct": round(wins["P1"] / n * 100, 1)},
            "P2": {"wins": wins["P2"], "pct": round(wins["P2"] / n * 100, 1)},
        },
        "score_distribution": dict(score_distribution.most_common()),
        "total_sets": {
            "P1": {"won": sets_won["P1"], "lost": sets_won["P2"]},
            "P2": {"won": sets_won["P2"], "lost": sets_won["P1"]},
        },
        "avg_stats": avg_stats,
        "total_stats": {tag: dict(total_stats[tag]) for tag in ("P1", "P2")},
        "match_length": {
            "avg_points": avg_points,
            "min_points": min_points if min_points != float("inf") else 0,
            "max_points": max_points,
            "avg_duration_min": avg_duration_min,
            "avg_sets": avg_sets,
        },
        "rally_distribution": rally_buckets,
        "win_rate_progression": win_rate_progression,
        "set_score_frequency": dict(
            Counter(set_score_frequency).most_common(10)
        ),
    }
