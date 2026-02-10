"""
Rutas de autenticación: registro, login, perfil.

Endpoints:
  POST /api/auth/register  →  Crear nuevo usuario
  POST /api/auth/login     →  Autenticar y devolver JWT
  GET  /api/auth/me        →  Datos del usuario autenticado (requiere token)
"""

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

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


# ─── POST /api/auth/register ──────────────────────────────────
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

    # Crear usuario
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


# ─── POST /api/auth/login ─────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Autentica al usuario por username o email y devuelve un JWT."""

    # Buscar por username o email
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


# ─── GET /api/auth/me ─────────────────────────────────────────
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
