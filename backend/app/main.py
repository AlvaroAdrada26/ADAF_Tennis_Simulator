"""
FastAPI backend para el ADAF Tennis Simulator.

- Sirve páginas HTML con Jinja2 (SSR) en /, /menu, /simulacion, /resultados...
- Sirve archivos estáticos en /static (css/js/images)
- Expone la API JSON en /api (ej: POST /api/simulate_match)
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.routes.pages import router as pages_router
from backend.app.routes.api import router as api_router
from backend.app.auth.routes import router as auth_router


# ------------------------------------------------------------
# Paths (para que funcione aunque ejecutes uvicorn desde distintos sitios)
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]  # .../ADAF_TENNIS_SIMULATOR
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


# ------------------------------------------------------------
# App
# ------------------------------------------------------------
app = FastAPI(
    title="ADAF Tennis Simulator",
    description="Simulador estadístico de tenis (FastAPI + Jinja2).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # luego puedes restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Routers
app.include_router(pages_router)                 # páginas HTML
app.include_router(api_router, prefix="/api")    # API JSON bajo /api
app.include_router(auth_router, prefix="/api")   # Auth bajo /api/auth
