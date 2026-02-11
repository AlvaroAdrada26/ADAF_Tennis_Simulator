from pydantic import BaseModel
from typing import Dict, Optional


class JugadorCreate(BaseModel):
    nombre: str
    apellidos: str
    edad: int
    altura: int
    nacionalidad: str
    brazo: str  # "Derecho" | "Izquierdo"
    atributos: Dict[str, int]


class JugadorOut(BaseModel):
    id: int
    nombre: str
    apellido: str
    nacionalidad: Optional[str] = None
    altura_cm: Optional[int] = None
    brazo_bueno: Optional[str] = None
    attr_primer_saque: Optional[int] = None
    attr_segundo_saque: Optional[int] = None
    attr_resto: Optional[int] = None
    attr_derecha: Optional[int] = None
    attr_reves: Optional[int] = None
    attr_movilidad: Optional[int] = None
    attr_consistencia: Optional[int] = None
    attr_clutch: Optional[int] = None
    attr_fisico: Optional[int] = None

    class Config:
        from_attributes = True
