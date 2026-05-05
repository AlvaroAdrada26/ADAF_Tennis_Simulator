# backend/app/estrategico/store.py
"""Almacén en memoria de sesiones del Modo Estratégico."""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, Optional

from .models import EstrategicoSession

# Diccionario global de sesiones activas
_sessions: Dict[str, EstrategicoSession] = {}

# Timeout: sesiones inactivas más de 2 horas se eliminan
SESSION_TIMEOUT_HOURS = 2


def get_session(session_id: str) -> Optional[EstrategicoSession]:
    return _sessions.get(session_id)


def create_session(session: EstrategicoSession) -> None:
    _sessions[session.session_id] = session


def delete_session(session_id: str) -> bool:
    return _sessions.pop(session_id, None) is not None


def cleanup_expired() -> int:
    """Elimina sesiones inactivas. Devuelve cuántas se eliminaron."""
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=SESSION_TIMEOUT_HOURS)
    expired = [sid for sid, s in _sessions.items() if s.last_activity < cutoff]
    for sid in expired:
        del _sessions[sid]
    return len(expired)
