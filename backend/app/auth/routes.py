"""
Rutas de autenticación: registro, login, perfil.

Endpoints:
  POST /api/auth/register  →  Crear nuevo usuario
  POST /api/auth/login     →  Autenticar y devolver JWT
  GET  /api/auth/me        →  Datos del usuario autenticado (requiere token)
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.auth.database import get_db
from backend.app.auth.models import Usuario
from backend.app.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from backend.app.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from backend.app.matches.models import Partido
from backend.app.players.models import Jugador

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


# -- POST /api/auth/register --
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Registra un nuevo usuario."""

    # Comprobar duplicados
    if db.query(Usuario).filter(Usuario.username == body.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya está en uso.",
        )

    if db.query(Usuario).filter(Usuario.email == body.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado.",
        )

    # crear usuario
    user = Usuario(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        nombre=body.nombre,
        apellido=body.apellido,
        nacionalidad=body.nacionalidad,
        genero=body.genero,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# -- POST /api/auth/login --
@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Autentica al usuario por username o email y devuelve un JWT."""

    # buscar por username o email
    user = (
        db.query(Usuario)
        .filter(
            (Usuario.username == body.identifier)
            | (Usuario.email == body.identifier)
        )
        .first()
    )

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas.",
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta cuenta está desactivada.",
        )

    token = create_access_token(data={"sub": str(user.id), "username": user.username})

    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


# -- GET /api/auth/me --
@router.get("/me", response_model=UserOut)
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """Devuelve los datos del usuario autenticado."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso requerido.",
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
        )

    user_id = payload.get("sub")
    user = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    return user


# -- GET /api/auth/me/matches --
@router.get("/me/matches")
def get_my_matches(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """Devuelve el historial de partidos simulados por el usuario autenticado."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso requerido.",
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
        )

    user_id = int(payload.get("sub"))

    partidos = (
        db.query(Partido)
        .filter(Partido.id_usuario_creador == user_id, Partido.activo == True)
        .order_by(Partido.fecha_jugado.desc())
        .all()
    )

    resultado = []
    for p in partidos:
        j1 = db.query(Jugador).filter(Jugador.id == p.id_jugador_1).first()
        j2 = db.query(Jugador).filter(Jugador.id == p.id_jugador_2).first()

        nombre_j1 = f"{j1.nombre} {j1.apellido}" if j1 else "Desconocido"
        nombre_j2 = f"{j2.nombre} {j2.apellido}" if j2 else "Desconocido"

        # determinar nombre del ganador
        if p.id_ganador == p.id_jugador_1:
            nombre_ganador = nombre_j1
        elif p.id_ganador == p.id_jugador_2:
            nombre_ganador = nombre_j2
        else:
            nombre_ganador = "—"

        superficie_icons = {"Dura": "🏟️", "Arcilla": "🧱", "Hierba": "🌿"}

        resultado.append({
            "id": p.id,
            "jugador_1": nombre_j1,
            "jugador_2": nombre_j2,
            "marcador_final": p.marcador_final,
            "ganador": nombre_ganador,
            "superficie": p.superficie or "—",
            "superficie_icon": superficie_icons.get(p.superficie, ""),
            "formato_sets": p.formato_sets,
            "fecha": p.fecha_jugado.strftime("%d/%m/%Y %H:%M") if p.fecha_jugado else "—",
            "duracion_minutos": p.duracion_minutos,
        })

    return resultado


# -- GET /api/auth/me/players --
@router.get("/me/players")
def get_my_players(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """Devuelve solo los jugadores creados por el usuario autenticado."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso requerido.",
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
        )

    user_id = int(payload.get("sub"))

    jugadores = (
        db.query(Jugador)
        .filter(Jugador.id_creador == user_id, Jugador.activo == True)
        .order_by(Jugador.created_at.desc())
        .all()
    )

    brazo_map = {"R": "Diestro", "L": "Zurdo"}

    return [
        {
            "id": j.id,
            "nombre": j.nombre,
            "apellido": j.apellido,
            "nombre_completo": f"{j.nombre} {j.apellido}",
            "nacionalidad": j.nacionalidad or "—",
            "altura_cm": j.altura_cm,
            "brazo_bueno": brazo_map.get(j.brazo_bueno, "—"),
            "attr_primer_saque": j.attr_primer_saque,
            "attr_segundo_saque": j.attr_segundo_saque,
            "attr_resto": j.attr_resto,
            "attr_derecha": j.attr_derecha,
            "attr_reves": j.attr_reves,
            "attr_movilidad": j.attr_movilidad,
            "attr_consistencia": j.attr_consistencia,
            "attr_clutch": j.attr_clutch,
            "attr_fisico": j.attr_fisico,
        }
        for j in jugadores
    ]
