# backend/app/estrategico/routes.py
"""Endpoints del Modo Estratégico (/api/estrategico/*)."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.simulator.models import Player
from backend.simulator.point import PointSimulator
from backend.simulator.scorekeeper import MatchScorekeeper
from backend.simulator.strategy import STRATEGY_MODIFIERS, VALID_STRATEGIES, get_modifiers

from .models import EstrategicoSession
from .store import get_session, create_session, delete_session, cleanup_expired
from .schemas import (
    EstrategicoStartRequest,
    EstrategicoNextPointRequest,
    EstrategicoSetStrategyRequest,
    EstrategicoEndRequest,
    EstrategicoSaveRequest,
)

router = APIRouter(prefix="/estrategico", tags=["estrategico"])


# ── helpers ───────────────────────────────────────────────
def _player_from_schema(data) -> Player:
    return Player(
        name=data.name,
        id=data.id,
        Primer_Saque=data.Primer_Saque,
        Segundo_Saque=data.Segundo_Saque,
        Fisico=data.Fisico,
        Estamina=data.Estamina,
        Consistencia=data.Consistencia,
        Clutch=data.Clutch,
        Momentum=data.Momentum,
        Derecha=data.Derecha,
        Reves=data.Reves,
        Resto=data.Resto,
        Movilidad=data.Movilidad,
    )


def _build_score_response(sk: MatchScorekeeper) -> Dict[str, Any]:
    return sk.get_score_snapshot()


# POST /api/estrategico/start
@router.post("/start")
def estrategico_start(req: EstrategicoStartRequest):
    # limpiar sesiones expiradas (oportunista)
    cleanup_expired()

    p1 = _player_from_schema(req.player1)
    p2 = _player_from_schema(req.player2)
    p1.reset_dynamic_state()
    p2.reset_dynamic_state()

    cfg = req.config or EstrategicoStartRequest.__fields__["config"].default
    best_of = cfg.best_of if cfg else 3
    tiebreak = cfg.tiebreak if cfg else True

    sk = MatchScorekeeper(p1, p2, best_of=best_of, tiebreak=tiebreak)

    session_id = str(uuid.uuid4())
    session = EstrategicoSession(
        session_id=session_id,
        player1=p1,
        player2=p2,
        scorekeeper=sk,
        coached_player=req.coached_player,
    )
    create_session(session)

    server_id, returner_id = sk.get_server_returner()

    return {
        "session_id": session_id,
        "coached_player": req.coached_player,
        "current_strategy": session.current_strategy,
        "score": _build_score_response(sk),
        "players": {"P1": p1.name, "P2": p2.name},
        "server_id": server_id,
    }


# POST /api/estrategico/next-point
@router.post("/next-point")
def estrategico_next_point(req: EstrategicoNextPointRequest):
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(404, "Sesión no encontrada")
    if session.match_finished:
        raise HTTPException(400, "El partido ya ha terminado")

    session.last_activity = datetime.utcnow()

    # cambio de estrategia en linea (opcional)
    if req.strategy:
        if req.strategy not in VALID_STRATEGIES:
            raise HTTPException(400, f"Estrategia inválida: {req.strategy}")
        session.current_strategy = req.strategy

    sk = session.scorekeeper
    server_id, returner_id = sk.get_server_returner()
    server_obj = sk.get_player(server_id)
    returner_obj = sk.get_player(returner_id)

    # determinar que estrategia va a cada jugador
    coached = session.coached_player
    coached_mods = get_modifiers(session.current_strategy)
    if server_id == coached:
        server_strategy = coached_mods
        returner_strategy = None
    else:
        server_strategy = None
        returner_strategy = coached_mods

    clutch = sk.is_clutch_point()
    bp = sk.is_break_point()

    tags = {"SACADOR": server_id, "RESTADOR": returner_id}
    ps = PointSimulator(
        server_obj, returner_obj,
        clutch=clutch,
        tags=tags,
        server_strategy=server_strategy,
        returner_strategy=returner_strategy,
    )
    result = ps.simulate(verbose=False)

    # Registrar resultado en scorekeeper
    events = sk.register_point(result.winner, result.stats.get("rally_shots", 0))

    # Enriquecer PointResult
    result.set_no = sk.current_set
    result.game_no = sk.game_no
    result.point_no = sk.point_no
    result.winner_id = events["winner_id"]
    result.server_id = events["server_id"]
    result.game_end = events["game_end"]
    result.set_end = events["set_end"]
    result.is_tiebreak = sk.is_tiebreak
    result.is_break_point = bp
    result.momentum_p1 = session.player1.Momentum
    result.momentum_p2 = session.player2.Momentum

    # Score after
    score_snap = sk.get_score_snapshot()
    result.score_after = {
        "set_scores": list(score_snap["set_scores"]),
        "games": score_snap["games"],
        "server_points": score_snap["points"].get(server_id, "0"),
        "returner_points": score_snap["points"].get(returner_id, "0"),
    }
    if sk.is_tiebreak:
        result.score_after["tiebreak_score"] = dict(sk.tb_points)

    names = {"P1": session.player1.name, "P2": session.player2.name}
    point_dict = result.to_dict(names)

    session.timeline.append(point_dict)

    if events["match_end"]:
        session.match_finished = True
        session.winner = sk.winner

    return {
        "point": point_dict,
        "score": score_snap,
        "current_strategy": session.current_strategy,
        "match_finished": session.match_finished,
        "winner": session.winner,
        "point_index": len(session.timeline) - 1,
        "stamina_p1": round(session.player1.Estamina, 2),
        "stamina_p2": round(session.player2.Estamina, 2),
        "momentum_p1": round(session.player1.Momentum, 2),
        "momentum_p2": round(session.player2.Momentum, 2),
    }


# POST /api/estrategico/set-strategy
@router.post("/set-strategy")
def estrategico_set_strategy(req: EstrategicoSetStrategyRequest):
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(404, "Sesión no encontrada")
    session.current_strategy = req.strategy
    session.last_activity = datetime.utcnow()
    return {"current_strategy": session.current_strategy}


# GET /api/estrategico/state/{session_id}
@router.get("/state/{session_id}")
def estrategico_state(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, "Sesión no encontrada")
    sk = session.scorekeeper
    return {
        "session_id": session.session_id,
        "coached_player": session.coached_player,
        "current_strategy": session.current_strategy,
        "score": _build_score_response(sk),
        "players": {"P1": session.player1.name, "P2": session.player2.name},
        "match_finished": session.match_finished,
        "winner": session.winner,
        "timeline_length": len(session.timeline),
        "stamina_p1": round(session.player1.Estamina, 2),
        "stamina_p2": round(session.player2.Estamina, 2),
        "momentum_p1": round(session.player1.Momentum, 2),
        "momentum_p2": round(session.player2.Momentum, 2),
    }


# POST /api/estrategico/end
@router.post("/end")
def estrategico_end(req: EstrategicoEndRequest):
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(404, "Sesión no encontrada")

    # Simular puntos restantes hasta que termine el partido
    while not session.match_finished:
        sk = session.scorekeeper
        server_id, returner_id = sk.get_server_returner()
        server_obj = sk.get_player(server_id)
        returner_obj = sk.get_player(returner_id)

        tags = {"SACADOR": server_id, "RESTADOR": returner_id}
        ps = PointSimulator(server_obj, returner_obj, clutch=sk.is_clutch_point(), tags=tags)
        result = ps.simulate(verbose=False)

        events = sk.register_point(result.winner, result.stats.get("rally_shots", 0))

        result.set_no = sk.current_set
        result.game_no = sk.game_no
        result.point_no = sk.point_no
        result.winner_id = events["winner_id"]
        result.server_id = events["server_id"]
        result.game_end = events["game_end"]
        result.set_end = events["set_end"]
        result.is_tiebreak = sk.is_tiebreak
        result.momentum_p1 = session.player1.Momentum
        result.momentum_p2 = session.player2.Momentum

        score_snap = sk.get_score_snapshot()
        result.score_after = {
            "set_games": score_snap["games"],
            "server_points": score_snap["points"].get(server_id, "0"),
            "returner_points": score_snap["points"].get(returner_id, "0"),
        }
        if sk.is_tiebreak:
            result.score_after["tiebreak_score"] = dict(sk.tb_points)

        names = {"P1": session.player1.name, "P2": session.player2.name}
        session.timeline.append(result.to_dict(names))

        if events["match_end"]:
            session.match_finished = True
            session.winner = sk.winner

    sk = session.scorekeeper
    return {
        "match_finished": True,
        "winner": session.winner,
        "score": _build_score_response(sk),
        "players": {"P1": session.player1.name, "P2": session.player2.name},
        "timeline": session.timeline,
        "set_scores": sk.set_scores,
    }


# POST /api/estrategico/save
@router.post("/save")
def estrategico_save(req: EstrategicoSaveRequest):
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(404, "Sesión no encontrada")
    if not session.match_finished:
        raise HTTPException(400, "El partido no ha terminado aún")

    sk = session.scorekeeper
    winner_id = session.winner
    winner_name = session.player1.name if winner_id == "P1" else session.player2.name

    result = {
        "players": {"P1": session.player1.name, "P2": session.player2.name},
        "winner_id": winner_id,
        "winner_name": winner_name,
        "sets_won": dict(sk.sets),
        "set_scores": sk.set_scores,
        "timeline": session.timeline,
        "best_of": sk.best_of,
        "tiebreak": sk.tiebreak_enabled,
    }

    return {"match_result": result, "message": "Datos del partido listos para guardar"}


# DELETE /api/estrategico/session/{session_id}
@router.delete("/session/{session_id}")
def estrategico_delete_session(session_id: str):
    if delete_session(session_id):
        return {"deleted": True}
    raise HTTPException(404, "Sesión no encontrada")
