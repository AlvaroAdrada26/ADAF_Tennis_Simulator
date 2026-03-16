"""
API routes para torneos: crear, simular rondas, consultar estado y estadísticas.
"""

import logging
import math
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.auth.database import get_db
from backend.app.auth.security import decode_access_token
from backend.app.matches.models import Partido, EstadisticaPartido
from backend.app.matches.stats import extract_player_stats
from backend.app.players.models import Jugador
from backend.app.tournaments.models import Torneo, TorneoPartido
from backend.simulator.api import run_match

router = APIRouter(prefix="/tournaments", tags=["tournaments"])
logger = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)


# ─── Schemas ───────────────────────────────────────────────────
class TournamentCreateRequest(BaseModel):
    nombre: str
    jugador_ids: List[int]           # IDs de BD de los jugadores
    superficie: Optional[str] = "Dura"
    formato_sets: int = 3
    tiebreak: bool = True


class SimulateRoundRequest(BaseModel):
    id_torneo: int


class SimulateMatchRequest(BaseModel):
    id_torneo: int
    torneo_partido_id: int


# ─── Helpers ───────────────────────────────────────────────────
_SUPERFICIE_NORM: dict[str, str] = {
    "dura": "Dura", "hard": "Dura",
    "tierra": "Arcilla", "arcilla": "Arcilla", "clay": "Arcilla",
    "hierba": "Hierba", "grass": "Hierba",
}


def _norm_superficie(raw: str | None) -> str | None:
    if not raw:
        return None
    return _SUPERFICIE_NORM.get(raw.lower(), raw if raw in {"Dura", "Arcilla", "Hierba"} else None)


def _format_marcador(set_scores: list) -> str:
    return ", ".join(f"{a}-{b}" for a, b in set_scores)


def _player_dict(j: Jugador) -> dict:
    """Convierte un Jugador ORM a dict para el simulador."""
    return {
        "name": f"{j.nombre} {j.apellido}",
        "id": str(j.id),
        "Primer_Saque": j.attr_primer_saque or 50,
        "Segundo_Saque": j.attr_segundo_saque or 50,
        "Fisico": j.attr_fisico or 50,
        "Estamina": j.attr_fisico or 50,
        "Consistencia": j.attr_consistencia or 50,
        "Clutch": j.attr_clutch or 50,
        "Momentum": j.attr_clutch or 50,
        "Derecha": j.attr_derecha or 50,
        "Reves": j.attr_reves or 50,
        "Resto": j.attr_resto or 50,
        "Movilidad": j.attr_movilidad or 50,
    }


# ─── POST /api/tournaments  — Crear torneo ────────────────────
@router.post("")
def crear_torneo(
    body: TournamentCreateRequest,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    n = len(body.jugador_ids)
    if n not in (4, 8, 16):
        raise HTTPException(status_code=400, detail="El número de jugadores debe ser 4, 8 o 16")

    if len(set(body.jugador_ids)) != n:
        raise HTTPException(status_code=400, detail="Hay jugadores duplicados")

    # Verificar que todos existen
    jugadores = db.query(Jugador).filter(Jugador.id.in_(body.jugador_ids), Jugador.activo == True).all()
    if len(jugadores) != n:
        raise HTTPException(status_code=404, detail="Alguno de los jugadores no existe")

    user_id = None
    if credentials:
        payload = decode_access_token(credentials.credentials)
        if payload:
            try:
                user_id = int(payload["sub"])
            except (KeyError, ValueError, TypeError):
                pass

    torneo = Torneo(
        nombre=body.nombre,
        id_usuario_creador=user_id,
        superficie=_norm_superficie(body.superficie),
        formato_sets=body.formato_sets,
        tiebreak_ultimo_set=body.tiebreak,
        num_jugadores=n,
        ids_jugadores=",".join(str(pid) for pid in body.jugador_ids),
    )
    db.add(torneo)
    db.flush()

    # Crear enfrentamientos de la primera ronda
    ronda = n // 2  # ej: 8 jugadores → ronda 4 (cuartos)
    ids = body.jugador_ids
    for i in range(0, n, 2):
        tp = TorneoPartido(
            id_torneo=torneo.id,
            ronda=ronda,
            posicion=(i // 2) + 1,
            id_jugador_1=ids[i],
            id_jugador_2=ids[i + 1],
        )
        db.add(tp)

    # Pre-crear slots de rondas siguientes (vacíos)
    ronda_actual = ronda // 2
    while ronda_actual >= 1:
        num_matches = ronda_actual
        for pos in range(1, num_matches + 1):
            tp = TorneoPartido(
                id_torneo=torneo.id,
                ronda=ronda_actual,
                posicion=pos,
            )
            db.add(tp)
        ronda_actual //= 2

    db.commit()
    db.refresh(torneo)

    return {"ok": True, "torneo_id": torneo.id, "nombre": torneo.nombre}


# ─── POST /api/tournaments/simulate-round ────────────────────
@router.post("/simulate-round")
def simular_ronda(
    body: SimulateRoundRequest,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    torneo = db.query(Torneo).filter(Torneo.id == body.id_torneo, Torneo.activo == True).first()
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    if torneo.completado:
        raise HTTPException(status_code=400, detail="El torneo ya está completado")

    user_id = None
    if credentials:
        payload = decode_access_token(credentials.credentials)
        if payload:
            try:
                user_id = int(payload["sub"])
            except (KeyError, ValueError, TypeError):
                pass

    # Encontrar la ronda pendiente más alta (la primera sin completar)
    pendientes = (
        db.query(TorneoPartido)
        .filter(
            TorneoPartido.id_torneo == torneo.id,
            TorneoPartido.completado == False,
            TorneoPartido.id_jugador_1.isnot(None),
            TorneoPartido.id_jugador_2.isnot(None),
        )
        .order_by(TorneoPartido.ronda.desc(), TorneoPartido.posicion)
        .all()
    )

    if not pendientes:
        raise HTTPException(status_code=400, detail="No hay partidos pendientes para simular")

    ronda_actual = pendientes[0].ronda
    partidos_ronda = [p for p in pendientes if p.ronda == ronda_actual]
    resultados = []

    for tp in partidos_ronda:
        j1 = db.query(Jugador).filter(Jugador.id == tp.id_jugador_1).first()
        j2 = db.query(Jugador).filter(Jugador.id == tp.id_jugador_2).first()

        result = run_match(
            player1_data=_player_dict(j1),
            player2_data=_player_dict(j2),
            config={
                "best_of": torneo.formato_sets,
                "tiebreak": torneo.tiebreak_ultimo_set,
            },
        )

        timeline = result.get("timeline", [])
        set_scores = result.get("set_scores", [])
        winner_tag = result.get("winner_id")
        id_ganador = tp.id_jugador_1 if winner_tag == "P1" else tp.id_jugador_2

        # Guardar partido en BD
        partido = Partido(
            id_jugador_1=tp.id_jugador_1,
            id_jugador_2=tp.id_jugador_2,
            id_ganador=id_ganador,
            id_usuario_creador=user_id,
            marcador_final=_format_marcador(set_scores),
            duracion_minutos=max(1, round(len(timeline) * 35 / 60)),
            superficie=torneo.superficie,
            formato_sets=torneo.formato_sets,
            tiebreak_ultimo_set=torneo.tiebreak_ultimo_set,
        )
        db.add(partido)
        db.flush()

        # Guardar estadísticas
        player_stats = extract_player_stats(timeline)
        for tag, db_id in [("P1", tp.id_jugador_1), ("P2", tp.id_jugador_2)]:
            s = player_stats[tag]
            est = EstadisticaPartido(
                id_partido=partido.id,
                id_jugador=db_id,
                id_usuario=user_id,
                **s,
            )
            db.add(est)

        # Actualizar torneo_partido
        tp.id_partido = partido.id
        tp.id_ganador = id_ganador
        tp.completado = True

        # Acumular el id del partido en la columna ids_partidos del torneo
        if torneo.ids_partidos:
            torneo.ids_partidos += "," + str(partido.id)
        else:
            torneo.ids_partidos = str(partido.id)

        # Avanzar ganador a la siguiente ronda
        if ronda_actual > 1:
            siguiente_ronda = ronda_actual // 2
            siguiente_pos = math.ceil(tp.posicion / 2)
            slot = (
                db.query(TorneoPartido)
                .filter(
                    TorneoPartido.id_torneo == torneo.id,
                    TorneoPartido.ronda == siguiente_ronda,
                    TorneoPartido.posicion == siguiente_pos,
                )
                .first()
            )
            if slot:
                if tp.posicion % 2 == 1:
                    slot.id_jugador_1 = id_ganador
                else:
                    slot.id_jugador_2 = id_ganador

        resultados.append({
            "torneo_partido_id": tp.id,
            "partido_id": partido.id,
            "ronda": ronda_actual,
            "posicion": tp.posicion,
            "jugador_1": {"id": j1.id, "nombre": f"{j1.nombre} {j1.apellido}"},
            "jugador_2": {"id": j2.id, "nombre": f"{j2.nombre} {j2.apellido}"},
            "ganador_id": id_ganador,
            "marcador": partido.marcador_final,
            "stats": player_stats,
        })

    # Si la ronda era la final (ronda == 1), marcar torneo como completado
    if ronda_actual == 1 and len(partidos_ronda) == 1:
        torneo.id_ganador = partidos_ronda[0].id_ganador
        torneo.completado = True

    db.commit()

    return {
        "ok": True,
        "ronda_simulada": ronda_actual,
        "resultados": resultados,
        "torneo_completado": torneo.completado,
        "ganador_torneo_id": torneo.id_ganador,
    }


# ─── Helper: simular un TorneoPartido ────────────────────────
def _simulate_tp(tp: TorneoPartido, torneo: Torneo, db: Session, user_id: int | None):
    """Simula un TorneoPartido individual. Devuelve dict de resultado."""
    j1 = db.query(Jugador).filter(Jugador.id == tp.id_jugador_1).first()
    j2 = db.query(Jugador).filter(Jugador.id == tp.id_jugador_2).first()

    result = run_match(
        player1_data=_player_dict(j1),
        player2_data=_player_dict(j2),
        config={
            "best_of": torneo.formato_sets,
            "tiebreak": torneo.tiebreak_ultimo_set,
        },
    )

    timeline = result.get("timeline", [])
    set_scores = result.get("set_scores", [])
    winner_tag = result.get("winner_id")
    id_ganador = tp.id_jugador_1 if winner_tag == "P1" else tp.id_jugador_2

    partido = Partido(
        id_jugador_1=tp.id_jugador_1,
        id_jugador_2=tp.id_jugador_2,
        id_ganador=id_ganador,
        id_usuario_creador=user_id,
        marcador_final=_format_marcador(set_scores),
        duracion_minutos=max(1, round(len(timeline) * 35 / 60)),
        superficie=torneo.superficie,
        formato_sets=torneo.formato_sets,
        tiebreak_ultimo_set=torneo.tiebreak_ultimo_set,
    )
    db.add(partido)
    db.flush()

    player_stats = extract_player_stats(timeline)
    for tag, db_id in [("P1", tp.id_jugador_1), ("P2", tp.id_jugador_2)]:
        s = player_stats[tag]
        est = EstadisticaPartido(
            id_partido=partido.id,
            id_jugador=db_id,
            id_usuario=user_id,
            **s,
        )
        db.add(est)

    tp.id_partido = partido.id
    tp.id_ganador = id_ganador
    tp.completado = True

    if torneo.ids_partidos:
        torneo.ids_partidos += "," + str(partido.id)
    else:
        torneo.ids_partidos = str(partido.id)

    # Avanzar ganador a la siguiente ronda
    if tp.ronda > 1:
        siguiente_ronda = tp.ronda // 2
        siguiente_pos = math.ceil(tp.posicion / 2)
        slot = (
            db.query(TorneoPartido)
            .filter(
                TorneoPartido.id_torneo == torneo.id,
                TorneoPartido.ronda == siguiente_ronda,
                TorneoPartido.posicion == siguiente_pos,
            )
            .first()
        )
        if slot:
            if tp.posicion % 2 == 1:
                slot.id_jugador_1 = id_ganador
            else:
                slot.id_jugador_2 = id_ganador

    # Si era la final, marcar torneo completado
    if tp.ronda == 1:
        torneo.id_ganador = id_ganador
        torneo.completado = True

    return {
        "torneo_partido_id": tp.id,
        "partido_id": partido.id,
        "ronda": tp.ronda,
        "posicion": tp.posicion,
        "jugador_1": {"id": j1.id, "nombre": f"{j1.nombre} {j1.apellido}"},
        "jugador_2": {"id": j2.id, "nombre": f"{j2.nombre} {j2.apellido}"},
        "ganador_id": id_ganador,
        "marcador": partido.marcador_final,
        "stats": player_stats,
    }


# ─── POST /api/tournaments/simulate-match  — Simular un partido suelto ──
@router.post("/simulate-match")
def simular_partido(
    body: SimulateMatchRequest,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    torneo = db.query(Torneo).filter(Torneo.id == body.id_torneo, Torneo.activo == True).first()
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    if torneo.completado:
        raise HTTPException(status_code=400, detail="El torneo ya está completado")

    user_id = None
    if credentials:
        payload = decode_access_token(credentials.credentials)
        if payload:
            try:
                user_id = int(payload["sub"])
            except (KeyError, ValueError, TypeError):
                pass

    tp = (
        db.query(TorneoPartido)
        .filter(
            TorneoPartido.id == body.torneo_partido_id,
            TorneoPartido.id_torneo == torneo.id,
        )
        .first()
    )
    if not tp:
        raise HTTPException(status_code=404, detail="Partido de torneo no encontrado")
    if tp.completado:
        raise HTTPException(status_code=400, detail="Este partido ya se ha jugado")
    if not tp.id_jugador_1 or not tp.id_jugador_2:
        raise HTTPException(status_code=400, detail="Faltan jugadores en este enfrentamiento")

    # Verify it belongs to the current pending round
    pendientes = (
        db.query(TorneoPartido)
        .filter(
            TorneoPartido.id_torneo == torneo.id,
            TorneoPartido.completado == False,
            TorneoPartido.id_jugador_1.isnot(None),
            TorneoPartido.id_jugador_2.isnot(None),
        )
        .order_by(TorneoPartido.ronda.desc())
        .all()
    )
    if not pendientes:
        raise HTTPException(status_code=400, detail="No hay partidos pendientes")
    ronda_pendiente = pendientes[0].ronda
    if tp.ronda != ronda_pendiente:
        raise HTTPException(status_code=400, detail="Este partido no pertenece a la ronda actual")

    resultado = _simulate_tp(tp, torneo, db, user_id)
    db.commit()

    return {
        "ok": True,
        "resultado": resultado,
        "torneo_completado": torneo.completado,
        "ganador_torneo_id": torneo.id_ganador,
    }


# ─── GET /api/tournaments/{id}  — Estado del torneo ──────────
@router.get("/{torneo_id}")
def get_torneo(torneo_id: int, db: Session = Depends(get_db)):
    torneo = db.query(Torneo).filter(Torneo.id == torneo_id, Torneo.activo == True).first()
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")

    # Obtener todos los partidos del torneo
    tp_list = (
        db.query(TorneoPartido)
        .filter(TorneoPartido.id_torneo == torneo_id)
        .order_by(TorneoPartido.ronda.desc(), TorneoPartido.posicion)
        .all()
    )

    # Recoger IDs de jugadores únicos
    player_ids = set()
    for tp in tp_list:
        if tp.id_jugador_1:
            player_ids.add(tp.id_jugador_1)
        if tp.id_jugador_2:
            player_ids.add(tp.id_jugador_2)
        if tp.id_ganador:
            player_ids.add(tp.id_ganador)
    if torneo.id_ganador:
        player_ids.add(torneo.id_ganador)

    jugadores = {
        j.id: {"id": j.id, "nombre": j.nombre, "apellido": j.apellido, "nacionalidad": j.nacionalidad}
        for j in db.query(Jugador).filter(Jugador.id.in_(player_ids)).all()
    }

    bracket = []
    for tp in tp_list:
        entry = {
            "id": tp.id,
            "ronda": tp.ronda,
            "posicion": tp.posicion,
            "jugador_1": jugadores.get(tp.id_jugador_1),
            "jugador_2": jugadores.get(tp.id_jugador_2),
            "ganador_id": tp.id_ganador,
            "completado": tp.completado,
            "partido_id": tp.id_partido,
            "marcador": None,
        }
        if tp.id_partido:
            partido = db.query(Partido).filter(Partido.id == tp.id_partido).first()
            if partido:
                entry["marcador"] = partido.marcador_final
        bracket.append(entry)

    return {
        "torneo": {
            "id": torneo.id,
            "nombre": torneo.nombre,
            "superficie": torneo.superficie,
            "formato_sets": torneo.formato_sets,
            "num_jugadores": torneo.num_jugadores,
            "completado": torneo.completado,
            "ganador": jugadores.get(torneo.id_ganador),
            "ids_jugadores": torneo.ids_jugadores,
            "ids_partidos": torneo.ids_partidos,
        },
        "bracket": bracket,
        "jugadores": jugadores,
    }


# ─── GET /api/tournaments/{id}/match/{partido_id}  — Stats de un partido ─
@router.get("/{torneo_id}/match/{partido_id}")
def get_torneo_match_stats(torneo_id: int, partido_id: int, db: Session = Depends(get_db)):
    partido = db.query(Partido).filter(Partido.id == partido_id).first()
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    j1 = db.query(Jugador).filter(Jugador.id == partido.id_jugador_1).first()
    j2 = db.query(Jugador).filter(Jugador.id == partido.id_jugador_2).first()

    stats = (
        db.query(EstadisticaPartido)
        .filter(EstadisticaPartido.id_partido == partido_id)
        .all()
    )
    stats_j1 = next((s for s in stats if s.id_jugador == partido.id_jugador_1), None)
    stats_j2 = next((s for s in stats if s.id_jugador == partido.id_jugador_2), None)

    def stat_block(s):
        if not s:
            return None
        pct_1er = round(s.primeros_saques_in / s.primeros_saques_total * 100) if s.primeros_saques_total else 0
        pct_bp = round(s.break_points_convertidos / s.break_points_oportunidades * 100) if s.break_points_oportunidades else 0
        return {
            "aces": s.aces,
            "dobles_faltas": s.dobles_faltas,
            "pct_primer_saque": pct_1er,
            "puntos_ganados_1er_saque": s.puntos_ganados_1er_saque,
            "puntos_ganados_2do_saque": s.puntos_ganados_2do_saque,
            "winners": s.winners,
            "errores_no_forzados": s.errores_no_forzados,
            "total_puntos_ganados": s.total_puntos_ganados,
            "break_points": f"{s.break_points_convertidos}/{s.break_points_oportunidades}",
            "pct_break_points": pct_bp,
        }

    return {
        "partido": {
            "id": partido.id,
            "marcador_final": partido.marcador_final,
            "id_ganador": partido.id_ganador,
        },
        "jugador_1": {
            "id": j1.id,
            "nombre": f"{j1.nombre} {j1.apellido}",
            "stats": stat_block(stats_j1),
        },
        "jugador_2": {
            "id": j2.id,
            "nombre": f"{j2.nombre} {j2.apellido}",
            "stats": stat_block(stats_j2),
        },
    }


# ─── GET /api/tournaments — Listar torneos del usuario ───────
@router.get("")
def listar_torneos(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    user_id = None
    if credentials:
        payload = decode_access_token(credentials.credentials)
        if payload:
            try:
                user_id = int(payload["sub"])
            except (KeyError, ValueError, TypeError):
                pass

    query = db.query(Torneo).filter(Torneo.activo == True)
    if user_id:
        query = query.filter(Torneo.id_usuario_creador == user_id)
    torneos = query.order_by(Torneo.fecha_creado.desc()).all()

    results = []
    for t in torneos:
        ganador = None
        if t.id_ganador:
            j = db.query(Jugador).filter(Jugador.id == t.id_ganador).first()
            if j:
                ganador = f"{j.nombre} {j.apellido}"
        results.append({
            "id": t.id,
            "nombre": t.nombre,
            "superficie": t.superficie,
            "num_jugadores": t.num_jugadores,
            "completado": t.completado,
            "ganador": ganador,
            "ids_jugadores": t.ids_jugadores,
            "ids_partidos": t.ids_partidos,
            "fecha": t.fecha_creado.isoformat() if t.fecha_creado else None,
        })

    return results
