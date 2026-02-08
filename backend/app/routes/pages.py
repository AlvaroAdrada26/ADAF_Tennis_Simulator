from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]  # .../ADAF_TENNIS_SIMULATOR
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/menu", response_class=HTMLResponse)
def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})


#@router.get("/simulacion", response_class=HTMLResponse)
#def simulacion(request: Request):
#    return templates.TemplateResponse("simulacion.html", {"request": request})


@router.get("/simulacion2", response_class=HTMLResponse)
def simulacion2(request: Request):
    return templates.TemplateResponse("simulacion2.html", {"request": request})


@router.get("/resultados", response_class=HTMLResponse)
def resultados(request: Request):
    return templates.TemplateResponse("resultados.html", {"request": request})
