from pydantic import BaseModel
from typing import Dict

class JugadorCreate(BaseModel):
    nombre: str
    apellidos: str
    edad: int
    altura: int
    nacionalidad: str
    brazo: str  # "Derecho" | "Izquierdo"
    atributos: Dict[str, int]
