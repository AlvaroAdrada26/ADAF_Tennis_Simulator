"""
Pydantic schemas para registro, login y respuestas de autenticación.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ─── Registro ──────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido: Optional[str] = Field(None, max_length=100)
    nacionalidad: Optional[str] = Field(None, max_length=50)
    genero: Optional[str] = Field(None, max_length=20)


# ─── Login ─────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Username o email")
    password: str


# ─── Respuestas ────────────────────────────────────────────────
class UserOut(BaseModel):
    id: int
    username: str
    email: str
    nombre: str
    apellido: Optional[str] = None
    nacionalidad: Optional[str] = None
    genero: Optional[str] = None
    foto_perfil_url: Optional[str] = None
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
