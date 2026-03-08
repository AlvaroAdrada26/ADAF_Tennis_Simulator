"""
Módulo de extracción de estadísticas por jugador a partir del timeline del partido.

Procesa la lista de puntos (timeline) generada por TennisMatch.play()
y produce un diccionario de estadísticas por jugador ("P1" y "P2"),
listo para insertarse en la tabla `estadisticas_partido`.
"""

from __future__ import annotations
from typing import Any, Dict, List


def extract_player_stats(timeline: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """
    Recorre el timeline punto a punto y acumula estadísticas por jugador.

    Parámetros
    ----------
    timeline : list[dict]
        Lista de puntos ya serializados (.to_dict()) con claves:
          server_id, winner ("P1"/"P2"), reason, stats, game_end,
          is_break_point, is_tiebreak …

    Retorna
    -------
    dict con claves "P1" y "P2", cada una conteniendo:
        aces, dobles_faltas,
        primeros_saques_in, primeros_saques_total,
        puntos_ganados_1er_saque, puntos_ganados_2do_saque,
        winners, errores_no_forzados,
        puntos_ganados_resto, total_puntos_ganados,
        break_points_convertidos, break_points_oportunidades
    """
    template = {
        "aces": 0,
        "dobles_faltas": 0,
        "primeros_saques_in": 0,
        "primeros_saques_total": 0,
        "puntos_ganados_1er_saque": 0,
        "puntos_ganados_2do_saque": 0,
        "winners": 0,
        "errores_no_forzados": 0,
        "puntos_ganados_resto": 0,
        "total_puntos_ganados": 0,
        "break_points_convertidos": 0,
        "break_points_oportunidades": 0,
    }

    stats = {
        "P1": dict(template),
        "P2": dict(template),
    }

    for pt in timeline:
        server_id = pt.get("server_id")          # "P1" o "P2"
        winner_id = pt.get("winner")              # "P1" o "P2"
        reason = pt.get("reason", "")
        pt_stats = pt.get("stats", {})
        game_end = pt.get("game_end", False)
        is_bp = pt.get("is_break_point", False)
        is_tb = pt.get("is_tiebreak", False)

        if not server_id or not winner_id:
            continue

        returner_id = "P2" if server_id == "P1" else "P1"
        first_in = pt_stats.get("first_in", 0)
        second_total = pt_stats.get("second_total", 0)

        # ── Servicio: acumular para el sacador ──
        stats[server_id]["primeros_saques_total"] += pt_stats.get("first_total", 0)
        stats[server_id]["primeros_saques_in"] += first_in

        # ── Aces y dobles faltas ──
        if reason == "ace":
            stats[server_id]["aces"] += 1
        if reason == "doble_falta":
            stats[server_id]["dobles_faltas"] += 1

        # ── Puntos ganados al servicio (1er y 2do saque) ──
        if winner_id == server_id:
            if first_in:
                stats[server_id]["puntos_ganados_1er_saque"] += 1
            elif second_total > 0:
                stats[server_id]["puntos_ganados_2do_saque"] += 1

        # ── Puntos ganados al resto ──
        if winner_id == returner_id:
            stats[returner_id]["puntos_ganados_resto"] += 1

        # ── Total de puntos ganados ──
        stats[winner_id]["total_puntos_ganados"] += 1

        # ── Winners (el rival no llega) ──
        if reason == "no_llega":
            stats[winner_id]["winners"] += 1

        # ── Errores no forzados (error_resto o error_golpe del perdedor) ──
        loser_id = "P2" if winner_id == "P1" else "P1"
        if reason in ("error_resto", "error_golpe"):
            stats[loser_id]["errores_no_forzados"] += 1

        # ── Break points (solo en juegos normales, no tie-break) ──
        if is_bp and not is_tb:
            # La oportunidad es del restador
            stats[returner_id]["break_points_oportunidades"] += 1
            # Convertido si el restador ganó el punto Y el juego terminó
            if winner_id == returner_id and game_end:
                stats[returner_id]["break_points_convertidos"] += 1

    return stats
