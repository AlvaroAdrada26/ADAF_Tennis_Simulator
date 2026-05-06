"""
FastAPI backend para el ADAF Tennis Simulator.

- Sirve páginas HTML con Jinja2 (SSR) en /, /menu, /simulacion, /resultados...
- Sirve archivos estáticos en /static (css/js/images)
- Expone la API JSON en /api (ej: POST /api/simulate_match)
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.routes.pages import router as pages_router
from backend.app.routes.api import router as api_router
from backend.app.auth.routes import router as auth_router
from backend.app.players.routes import router as jugadores_router
from backend.app.matches.routes import router as matches_router
from backend.app.tournaments.routes import router as tournaments_router
from backend.app.estrategico import estrategico_router
from backend.app.bigdata import bigdata_router





# ------------------------------------------------------------
# Paths (para que funcione aunque ejecutes uvicorn desde distintos sitios)
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]  # .../ADAF_TENNIS_SIMULATOR
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

error_templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


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
app.include_router(jugadores_router, prefix="/api")  # Jugadores bajo /api/players
app.include_router(matches_router, prefix="/api")    # Partidos bajo /api/matches
app.include_router(tournaments_router, prefix="/api")  # Torneos bajo /api/tournaments
app.include_router(estrategico_router, prefix="/api")    # Estratégico bajo /api/estrategico
app.include_router(bigdata_router, prefix="/api/bigdata")  # Big Data bajo /api/bigdata


# ------------------------------------------------------------
# Error handlers
# ------------------------------------------------------------
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Only render HTML for browser page requests (not /api calls)
    if request.url.path.startswith("/api"):
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    if exc.status_code == 404:
        return error_templates.TemplateResponse(
            "errors/404.html", {"request": request}, status_code=404
        )
    return error_templates.TemplateResponse(
        "errors/500.html", {"request": request}, status_code=exc.status_code
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if request.url.path.startswith("/api"):
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Internal server error"}, status_code=500)
    return error_templates.TemplateResponse(
        "errors/500.html", {"request": request}, status_code=500
    )
