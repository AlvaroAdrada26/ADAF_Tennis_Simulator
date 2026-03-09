from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]  # .../ADAF_TENNIS_SIMULATOR
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ─── Helpers ───────────────────────────────────────────────────────────────
def _placeholder(request: Request, title: str, active: str):
    """Render a generic 'coming soon' page."""
    return templates.TemplateResponse(
        "placeholder.html",
        {"request": request, "active_page": active, "page_title": title},
    )


# ─── Páginas principales ──────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "active_page": "home"}
    )


@router.get("/menu", response_class=HTMLResponse)
def menu(request: Request):
    return templates.TemplateResponse(
        "menu.html", {"request": request, "active_page": "menu"}
    )


@router.get("/simulacion2", response_class=HTMLResponse)
def simulacion2(request: Request):
    return templates.TemplateResponse(
        "simulacion2.html", {"request": request, "active_page": "simulacion"}
    )


@router.get("/simulacion-legacy", response_class=HTMLResponse)
def simulacion_legacy(request: Request):
    return templates.TemplateResponse(
        "simulacionExcremento.html", {"request": request, "active_page": "simulacion"}
    )


@router.get("/resultados", response_class=HTMLResponse)
def resultados(request: Request):
    return templates.TemplateResponse(
        "resultados.html", {"request": request, "active_page": "simulacion"}
    )


@router.get("/crear-jugador", response_class=HTMLResponse)
def crear_jugador(request: Request):
    return templates.TemplateResponse(
        "crear_jugador.html", {"request": request, "active_page": "crear_jugador"}
    )


@router.get("/crear-partido", response_class=HTMLResponse)
def crear_partido(request: Request):
    return templates.TemplateResponse(
        "crear_partido.html", {"request": request, "active_page": "crear_partido"}
    )


@router.get("/partido-rapido", response_class=HTMLResponse)
def partido_rapido(request: Request):
    return templates.TemplateResponse(
        "partido_rapido.html", {"request": request, "active_page": "partido_rapido"}
    )


@router.get("/simulacion-rapida", response_class=HTMLResponse)
def simulacion_rapida(request: Request):
    return templates.TemplateResponse(
        "simulacion_rapida.html", {"request": request, "active_page": "simulacion_rapida"}
    )


# ─── Autenticación ────────────────────────────────────────────────────────
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html", {"request": request, "active_page": "login"}
    )


@router.get("/registro", response_class=HTMLResponse)
def registro_page(request: Request):
    return templates.TemplateResponse(
        "registro.html", {"request": request, "active_page": "registro"}
    )


# ─── Sidebar: Estadísticas, Configuración, Historial ──────────────────────
@router.get("/estadisticas", response_class=HTMLResponse)
def estadisticas(request: Request):
    return _placeholder(request, "Estadísticas", "estadisticas")


@router.get("/configuracion", response_class=HTMLResponse)
def configuracion(request: Request):
    return _placeholder(request, "Configuración", "configuracion")


@router.get("/configuracion/avanzado", response_class=HTMLResponse)
def configuracion_avanzado(request: Request):
    return _placeholder(request, "Configuración Avanzada", "configuracion")


@router.get("/historial", response_class=HTMLResponse)
def historial(request: Request):
    return _placeholder(request, "Historial de Partidos", "simulacion")


# ─── Header / Footer links ────────────────────────────────────────────────
@router.get("/documentacion", response_class=HTMLResponse)
def documentacion(request: Request):
    return _placeholder(request, "Documentación", "home")


@router.get("/creditos", response_class=HTMLResponse)
def creditos(request: Request):
    return _placeholder(request, "Créditos", "home")


@router.get("/sobre-tfg", response_class=HTMLResponse)
def sobre_tfg(request: Request):
    return _placeholder(request, "Sobre el TFG", "home")


@router.get("/contacto", response_class=HTMLResponse)
def contacto(request: Request):
    return _placeholder(request, "Contacto", "home")


@router.get("/faqs", response_class=HTMLResponse)
def faqs(request: Request):
    return _placeholder(request, "Preguntas Frecuentes", "home")


@router.get("/tutoriales", response_class=HTMLResponse)
def tutoriales(request: Request):
    return _placeholder(request, "Tutoriales", "home")


@router.get("/analisis", response_class=HTMLResponse)
def analisis(request: Request):
    return _placeholder(request, "Análisis", "estadisticas")


@router.get("/api-docs", response_class=HTMLResponse)
def api_docs_page(request: Request):
    return _placeholder(request, "API Docs", "home")


@router.get("/ejemplos", response_class=HTMLResponse)
def ejemplos(request: Request):
    return _placeholder(request, "Ejemplos", "home")


@router.get("/metodologia", response_class=HTMLResponse)
def metodologia(request: Request):
    return _placeholder(request, "Metodología", "home")


@router.get("/soporte", response_class=HTMLResponse)
def soporte(request: Request):
    return _placeholder(request, "Soporte", "home")


@router.get("/privacidad", response_class=HTMLResponse)
def privacidad(request: Request):
    return _placeholder(request, "Política de Privacidad", "home")


@router.get("/terminos", response_class=HTMLResponse)
def terminos(request: Request):
    return _placeholder(request, "Términos de Uso", "home")


@router.get("/licencia", response_class=HTMLResponse)
def licencia(request: Request):
    return _placeholder(request, "Licencia", "home")
