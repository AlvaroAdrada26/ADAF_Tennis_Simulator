from typing import Optional
from pydantic import BaseModel, Field


class BigDataPlayerData(BaseModel):
    name: str
    id: str
    Primer_Saque: float
    Segundo_Saque: float
    Fisico: float
    Estamina: float
    Consistencia: float
    Clutch: float
    Momentum: float
    Derecha: float
    Reves: float
    Resto: float
    Movilidad: float


class BigDataConfigData(BaseModel):
    best_of: int = 3
    tiebreak: bool = True
    seed: Optional[int] = None
    superficie: Optional[str] = None


class BigDataRequest(BaseModel):
    player1: BigDataPlayerData
    player2: BigDataPlayerData
    config: Optional[BigDataConfigData] = None
    num_matches: int = Field(ge=10, le=10000, default=100)
