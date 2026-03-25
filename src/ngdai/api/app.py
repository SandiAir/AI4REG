"""FastAPI Application - Haupteinstiegspunkt fuer den Web-Server."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="ngdai",
    description="Wissensbasierte Analyseplattform fuer die deutsche Netzentgeltregulierung",
    version="0.1.0",
)

# Static files und Templates
STATIC_DIR = Path(__file__).parent.parent / "web" / "static"
TEMPLATE_DIR = Path(__file__).parent.parent / "web" / "templates"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


# ── Health Check ────────────────────────────────────────────

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


# ── Web Routes ──────────────────────────────────────────────

@app.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
