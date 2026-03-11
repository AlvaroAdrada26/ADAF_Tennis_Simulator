"""
Utilidades para extraer estadísticas de partido a partir del timeline punto a punto.
"""
from typing import Any, Dict, List


def extract_player_stats(timeline: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """
    Recorre el timeline y acumula las estadísticas para P1 y P2.

    Devuelve un dict con la forma:
        {
            "P1": { "aces": ..., "dobles_faltas": ..., ... },
            "P2": { ... },
        }
    """
    base = dict(
        aces=0,
        dobles_faltas=0,
        primeros_saques_in=0,
        primeros_saques_total=0,
        puntos_ganados_1er_saque=0,
        puntos_ganados_2do_saque=0,
        winners=0,
        errores_no_forzados=0,
        puntos_ganados_resto=0,
        total_puntos_ganados=0,
        break_points_convertidos=0,
        break_points_oportunidades=0,
    )
    stats: Dict[str, Dict[str, int]] = {
        "P1": dict(**base),
        "P2": dict(**base),
    }

    for pt in timeline:
        server = pt.get("server_id")
        winner = pt.get("winner")        # "winner_id" no existe en el dict; la clave es "winner"
        reason = pt.get("reason", "")
        s = pt.get("stats") or {}

        for tag in ("P1", "P2"):
            st = stats[tag]
            is_server = server == tag
            won = winner == tag

            if won:
                st["total_puntos_ganados"] += 1

            if is_server:
                first_in = s.get("first_in", 0)
                first_total = s.get("first_total", 0)
                st["primeros_saques_in"] += first_in
                st["primeros_saques_total"] += first_total

                if reason == "ace" and won:
                    st["aces"] += 1
                if reason == "doble_falta" and not won:
                    st["dobles_faltas"] += 1

                if won:
                    if first_in > 0:
                        st["puntos_ganados_1er_saque"] += 1
                    else:
                        st["puntos_ganados_2do_saque"] += 1
            else:
                # Restador
                if won:
                    st["puntos_ganados_resto"] += 1

            # Winners: golpe en el rally que el rival no pudo alcanzar
            # (aces ya se cuentan por separado; "no_llega" en fase de rally es el winner real)
            if won and reason == "no_llega":
                st["winners"] += 1

            # Errores no forzados: fallo en el resto o en el rally (cualquier jugador)
            if not won and reason in ("error_golpe", "error_resto"):
                st["errores_no_forzados"] += 1

            # Break points: solo en juegos normales (no tie-break), desde perspectiva del restador
            if not is_server and not pt.get("is_tiebreak", False):
                if pt.get("is_break_point", False):
                    st["break_points_oportunidades"] += 1
                    if won:
                        st["break_points_convertidos"] += 1

    return stats
