from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.database import get_db
from backend.app.auth.models import Usuario
from backend.app.auth.security import decode_access_token
from backend.app.players.models import Jugador
from backend.app.players.schemas import JugadorCreate, JugadorOut
from backend.app.auth.routes import bearer_scheme

router = APIRouter(prefix="/players", tags=["players"])


# ─── GET /api/players ──────────────────────────────────────────
@router.get("", response_model=List[JugadorOut])
def listar_jugadores(
    credentials=Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """Devuelve todos los jugadores del usuario autenticado."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    user_id = payload.get("sub")
    jugadores = (
        db.query(Jugador)
        .filter(Jugador.id_creador == int(user_id), Jugador.activo == True)
        .order_by(Jugador.nombre)
        .all()
    )
    return jugadores


@router.post("", status_code=status.HTTP_201_CREATED)
def crear_jugador(
    body: JugadorCreate,
    credentials=Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")

    usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    jugador = Jugador(
        nombre=body.nombre,
        apellido=body.apellidos,
        nacionalidad=body.nacionalidad[:3].upper() if body.nacionalidad else None,
        altura_cm=body.altura,
        brazo_bueno="L" if body.brazo == "Izquierdo" else "R",
        id_creador=usuario.id,

        attr_primer_saque=body.atributos["primer_saque"],
        attr_segundo_saque=body.atributos["segundo_saque"],
        attr_resto=body.atributos["resto"],
        attr_derecha=body.atributos["derecha"],
        attr_reves=body.atributos["reves"],
        attr_movilidad=body.atributos["movilidad"],
        attr_consistencia=body.atributos["consistencia"],
        attr_clutch=body.atributos["clutch"],
        attr_fisico=body.atributos["fisico"],
    )

    db.add(jugador)
    db.commit()
    db.refresh(jugador)

    return {"id": jugador.id, "mensaje": "Jugador creado correctamente"}
