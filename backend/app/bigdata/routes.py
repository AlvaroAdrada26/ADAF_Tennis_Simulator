"""
Endpoints del Modo Big Data.

- POST /simulate       → ejecución síncrona, devuelve JSON agregado.
- POST /simulate_stream → SSE con progreso en tiempo real + resultado final.
"""
from __future__ import annotations

import asyncio
import asyncio
import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.matches.stats import extract_player_stats
from backend.simulator.api import run_match

from .aggregation import aggregate_bigdata_stats
from .schemas import BigDataRequest

router = APIRouter()
logger = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)


def _run_single_match(request: BigDataRequest, seed_i: int | None) -> Dict[str, Any]:
    """Ejecuta un solo partido y devuelve el resultado con player_stats."""
    cfg = request.config.model_dump(exclude={"superficie"}) if request.config else {}
    if seed_i is not None:
        cfg["seed"] = seed_i

    result = run_match(
        player1_data=request.player1.model_dump(),
        player2_data=request.player2.model_dump(),
        config=cfg,
    )
    result["player_stats"] = extract_player_stats(result.get("timeline", []))
    return result


def _config_summary(request: BigDataRequest) -> Dict[str, Any]:
    if request.config:
        return {
            "best_of": request.config.best_of,
            "tiebreak": request.config.tiebreak,
            "superficie": request.config.superficie,
        }
    return {"best_of": 3, "tiebreak": True, "superficie": None}


# ── Endpoint síncrono ─────────────────────────────────────────────────────
@router.post("/simulate")
def bigdata_simulate(
    request: BigDataRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> Dict[str, Any]:
    """Simula N partidos y devuelve estadísticas agregadas."""
    base_seed = request.config.seed if request.config else None
    results = []

    for i in range(request.num_matches):
        seed_i = (base_seed + i) if base_seed is not None else None
        results.append(_run_single_match(request, seed_i))

    return aggregate_bigdata_stats(
        results,
        player1_name=request.player1.name,
        player2_name=request.player2.name,
        config_summary=_config_summary(request),
    )


# ── Endpoint con streaming SSE ────────────────────────────────────────────
@router.post("/simulate_stream")
async def bigdata_simulate_stream(
    request: BigDataRequest,
    http_request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    """Simula N partidos con progreso vía Server-Sent Events."""
    base_seed = request.config.seed if request.config else None
    progress_interval = max(1, request.num_matches // 100)

    async def generate():
        results = []
        wins = {"P1": 0, "P2": 0}

        for i in range(request.num_matches):
            # Detectar desconexion del cliente (abort)
            if await http_request.is_disconnected():
                return

            seed_i = (base_seed + i) if base_seed is not None else None
            # Ejecutar en threadpool para no bloquear el event loop
            result = await asyncio.to_thread(_run_single_match, request, seed_i)
            results.append(result)

            winner_id = result.get("winner_id", "P1")
            wins[winner_id] += 1

            # Enviar progreso periódicamente
            if (i + 1) % progress_interval == 0 or (i + 1) == request.num_matches:
                total_done = i + 1
                progress = {
                    "type": "progress",
                    "current": total_done,
                    "total": request.num_matches,
                    "pct": round(total_done / request.num_matches * 100, 1),
                    "wins_p1": wins["P1"],
                    "wins_p2": wins["P2"],
                    "p1_pct": round(wins["P1"] / total_done * 100, 1),
                    "p2_pct": round(wins["P2"] / total_done * 100, 1),
                }
                yield f"data: {json.dumps(progress)}\n\n"

        # Resultado final
        aggregated = aggregate_bigdata_stats(
            results,
            player1_name=request.player1.name,
            player2_name=request.player2.name,
            config_summary=_config_summary(request),
        )
        yield f"data: {json.dumps({'type': 'result', 'data': aggregated})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
