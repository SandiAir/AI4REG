"""FastAPI Application - Haupteinstiegspunkt fuer den Web-Server."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

logger = logging.getLogger("ngdai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: DB-Tabellen und Grunddaten sicherstellen."""
    try:
        from ngdai.db.engine import get_engine
        from ngdai.db.models import Base

        engine = get_engine()
        Base.metadata.create_all(engine)
        logger.info("Datenbank-Tabellen sichergestellt.")

        from ngdai.dimensions.registry import load_dimension_types
        from ngdai.definitions.service import load_fact_definitions, load_directory_definitions

        load_dimension_types()
        load_fact_definitions()
        load_directory_definitions()
        logger.info("Grunddaten geladen.")
    except Exception as e:
        logger.warning("Startup-Init fehlgeschlagen (App startet trotzdem): %s", e)

    yield


app = FastAPI(
    title="ngdai",
    description="Wissensbasierte Analyseplattform fuer die deutsche Netzentgeltregulierung",
    version="0.1.0",
    lifespan=lifespan,
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


# ── Dashboard ──────────────────────────────────────────────

@app.get("/")
def dashboard(request: Request):
    """Dashboard mit Live-Stats via HTMX."""
    return templates.TemplateResponse(request, "dashboard.html")


@app.get("/api/v1/stats", response_class=HTMLResponse)
def dashboard_stats():
    """HTMX-Fragment: Dashboard-Statistiken."""
    try:
        from ngdai.entities.service import count_entities
        from ngdai.ingestion.service import count_documents
        entity_count = count_entities()
        doc_count = count_documents()
    except Exception:
        entity_count = 0
        doc_count = 0

    try:
        from sqlalchemy import select, func
        from ngdai.db.engine import get_session
        from ngdai.db.models import FactModel
        session = get_session()
        fact_count = session.execute(select(func.count(FactModel.id))).scalar_one()
        session.close()
    except Exception:
        fact_count = 0

    return f"""
    <article class="stat-card"><h3>{entity_count:,}</h3><small>Netzbetreiber</small></article>
    <article class="stat-card"><h3>{doc_count:,}</h3><small>Dokumente</small></article>
    <article class="stat-card"><h3>{fact_count:,}</h3><small>Extrahierte Fakten</small></article>
    """


# ── Entities ───────────────────────────────────────────────

@app.get("/entities")
def entities_page(request: Request):
    return templates.TemplateResponse(request, "entities.html")


@app.get("/api/v1/entities", response_class=HTMLResponse)
def entities_list(
    search: str = Query("", description="Suchbegriff"),
    sector: str = Query("", description="Sektor-Filter"),
    page: int = Query(1, ge=1),
):
    """HTMX-Fragment: Entity-Tabelle."""
    from ngdai.entities.service import list_entities, find_entity_by_name, count_entities

    page_size = 50
    offset = (page - 1) * page_size

    if search:
        matches = find_entity_by_name(search, threshold=60, limit=page_size)
        entities = [e for e, _ in matches]
        total = len(matches)
    else:
        entities = list_entities(sector=sector or None, limit=page_size, offset=offset)
        total = count_entities(sector=sector or None)

    rows = ""
    for e in entities:
        sectors_str = ", ".join(e.sectors or [])
        rows += f"""<tr>
            <td><a href="/entities/{e.id}">{e.name}</a></td>
            <td>{sectors_str}</td>
            <td>{e.state}</td>
            <td>{e.city}</td>
            <td><code>{e.mastr_nr or ''}</code></td>
        </tr>"""

    # Pagination
    total_pages = max(1, (total + page_size - 1) // page_size)
    pagination = ""
    if total_pages > 1:
        pagination = '<nav><ul>'
        if page > 1:
            pagination += f'<li><a hx-get="/api/v1/entities?page={page-1}&sector={sector}&search={search}" hx-target="#entity-table">Zurück</a></li>'
        pagination += f'<li><span>Seite {page} von {total_pages} ({total} Ergebnisse)</span></li>'
        if page < total_pages:
            pagination += f'<li><a hx-get="/api/v1/entities?page={page+1}&sector={sector}&search={search}" hx-target="#entity-table">Weiter</a></li>'
        pagination += '</ul></nav>'

    return f"""
    <table>
        <thead><tr>
            <th>Name</th><th>Sektor</th><th>Bundesland</th><th>Ort</th><th>MaStR-Nr.</th>
        </tr></thead>
        <tbody>{rows}</tbody>
    </table>
    {pagination}
    """


@app.get("/entities/{entity_id}")
def entity_detail(request: Request, entity_id: str):
    from ngdai.entities.service import get_entity
    entity = get_entity(entity_id)
    return templates.TemplateResponse(request, "entity_detail.html", {"entity": entity})


# ── Documents ──────────────────────────────────────────────

@app.get("/documents")
def documents_page(request: Request):
    return templates.TemplateResponse(request, "documents.html")


@app.get("/api/v1/documents", response_class=HTMLResponse)
def documents_list(
    doc_type: str = Query("", description="Dokumenttyp-Filter"),
    page: int = Query(1, ge=1),
):
    """HTMX-Fragment: Dokumenten-Tabelle."""
    from ngdai.ingestion.service import list_documents, count_documents

    page_size = 50
    offset = (page - 1) * page_size
    docs = list_documents(document_type=doc_type or None, limit=page_size, offset=offset)
    total = count_documents()

    rows = ""
    for d in docs:
        status_color = {"ingested": "green", "extracted": "blue", "failed": "red"}.get(d.ingestion_status, "gray")
        rows += f"""<tr>
            <td>{d.original_filename}</td>
            <td>{d.document_type or '—'}</td>
            <td>{d.sector or '—'}</td>
            <td>{d.regulatory_period or '—'}</td>
            <td><mark style="background:{status_color};color:white;padding:2px 6px;border-radius:3px">{d.ingestion_status}</mark></td>
            <td>{d.char_count:,}</td>
        </tr>"""

    return f"""
    <table>
        <thead><tr>
            <th>Datei</th><th>Typ</th><th>Sektor</th><th>RP</th><th>Status</th><th>Zeichen</th>
        </tr></thead>
        <tbody>{rows}</tbody>
    </table>
    <p><small>{total} Dokumente insgesamt</small></p>
    """


# ── Query ──────────────────────────────────────────────────

@app.get("/query")
def query_page(request: Request, q: str = Query("", description="Frage")):
    return templates.TemplateResponse(request, "query.html", {"q": q})


@app.get("/api/v1/query", response_class=HTMLResponse)
def query_execute(q: str = Query(..., description="Frage")):
    """HTMX-Fragment: Query-Ergebnis."""
    if not q.strip():
        return "<p>Bitte eine Frage eingeben.</p>"

    try:
        from ngdai.query.service import execute_query
        result = execute_query(q)
        # Markdown → einfaches HTML (basic conversion)
        html = _markdown_to_html(result)
        return f'<article>{html}</article>'
    except Exception as e:
        return f'<article><p style="color:red">Fehler: {e}</p></article>'


# ── Admin API ─────────────────────────────────────────────

@app.get("/admin")
def admin_page(request: Request):
    return templates.TemplateResponse(request, "admin.html")


@app.post("/api/v1/admin/import-marktakteure")
def admin_import_marktakteure(
    sector: str = Query(..., description="strom oder gas"),
):
    """Marktakteure aus den mitgelieferten CSV-Dateien importieren."""
    from ngdai.core.config import PROJECT_ROOT
    from ngdai.entities.service import import_marktakteure_csv, invalidate_name_cache

    csv_map = {
        "strom": PROJECT_ROOT / "doc" / "daten" / "marktakteure" / "2026-03-23_OeffentlicheMarktakteure_Strom.csv",
        "gas": PROJECT_ROOT / "doc" / "daten" / "marktakteure" / "2026-03-23_OeffentlicheMarktakteur_Gas.csv",
    }

    csv_path = csv_map.get(sector)
    if not csv_path or not csv_path.exists():
        return {"error": f"CSV fuer Sektor '{sector}' nicht gefunden: {csv_path}"}

    count = import_marktakteure_csv(str(csv_path), sector)
    invalidate_name_cache()
    return {"status": "ok", "sector": sector, "imported": count}


@app.post("/api/v1/admin/ingest")
def admin_ingest(
    path: str = Query(..., description="Pfad relativ zum Projekt-Root"),
):
    """Dokumente aus einem Verzeichnis importieren."""
    from ngdai.core.config import PROJECT_ROOT
    from ngdai.ingestion.service import ingest_path

    full_path = PROJECT_ROOT / path
    if not full_path.exists():
        return {"error": f"Pfad nicht gefunden: {full_path}"}

    result = ingest_path(str(full_path))
    return {"status": "ok", "path": path, **result}


@app.post("/api/v1/admin/extract")
def admin_extract(
    document_id: str = Query("", description="Dokument-ID (leer = alle pending)"),
):
    """Fakten aus Dokumenten extrahieren."""
    from ngdai.extraction.service import extract_document, extract_all_pending

    if document_id:
        result = extract_document(document_id)
        return {"status": "ok", "mode": "single", **result}
    else:
        result = extract_all_pending()
        return {"status": "ok", "mode": "all_pending", **result}


@app.post("/api/v1/admin/seed")
def admin_seed():
    """Komplett-Import: Marktakteure + alle Dokumente ingesten."""
    from ngdai.core.config import PROJECT_ROOT
    from ngdai.entities.service import import_marktakteure_csv, invalidate_name_cache
    from ngdai.ingestion.service import ingest_path

    results = {}

    # 1. Marktakteure importieren
    for sector, filename in [
        ("strom", "2026-03-23_OeffentlicheMarktakteure_Strom.csv"),
        ("gas", "2026-03-23_OeffentlicheMarktakteur_Gas.csv"),
    ]:
        csv_path = PROJECT_ROOT / "doc" / "daten" / "marktakteure" / filename
        if csv_path.exists():
            count = import_marktakteure_csv(str(csv_path), sector)
            results[f"marktakteure_{sector}"] = count

    invalidate_name_cache()

    # 2. Dokumente ingesten
    doc_base = PROJECT_ROOT / "doc" / "daten"
    ingest_dirs = {
        "beschluesse_4rp": doc_base / "beschluesse" / "4rp",
        "beschluesse_3rp": doc_base / "beschluesse" / "3rp",
        "geschaeftsberichte_2024": doc_base / "geschaeftsberichte" / "2024",
    }

    for label, dir_path in ingest_dirs.items():
        if dir_path.exists():
            result = ingest_path(str(dir_path))
            results[f"ingest_{label}"] = result

    return {"status": "ok", "results": results}


@app.get("/api/v1/admin/files")
def admin_list_files():
    """Zeigt verfuegbare Daten-Verzeichnisse und Dateien."""
    from ngdai.core.config import PROJECT_ROOT

    doc_base = PROJECT_ROOT / "doc" / "daten"

    dirs_to_check = {
        "marktakteure": doc_base / "marktakteure",
        "geschaeftsberichte_2024": doc_base / "geschaeftsberichte" / "2024",
        "beschluesse_4rp": doc_base / "beschluesse" / "4rp",
        "beschluesse_3rp": doc_base / "beschluesse" / "3rp",
        "gerichtsurteile": doc_base / "gerichtsurteile",
        "preisblaetter": doc_base / "preisblaetter",
        "par23b": doc_base / "par23b",
        "par23c": doc_base / "par23c",
    }

    result = {"project_root": str(PROJECT_ROOT), "doc_base": str(doc_base)}

    for label, dir_path in dirs_to_check.items():
        if dir_path.exists():
            files = sorted([f.name for f in dir_path.iterdir() if f.is_file() and f.name != ".gitkeep"])
            result[label] = {"count": len(files), "files": files[:10], "path": str(dir_path)}
        else:
            result[label] = {"count": 0, "exists": False, "checked_path": str(dir_path)}

    return result


def _markdown_to_html(text: str) -> str:
    """Minimale Markdown→HTML-Konvertierung fuer Query-Ergebnisse."""
    import re
    lines = text.split("\n")
    html_lines = []
    in_table = False

    for line in lines:
        if line.startswith("|"):
            if not in_table:
                html_lines.append("<table>")
                in_table = True
            if line.startswith("|:") or line.startswith("|-"):
                continue  # Separator-Zeile
            cells = [c.strip() for c in line.split("|")[1:-1]]
            tag = "th" if not any("<td>" in h for h in html_lines[-3:] if "<" in h) else "td"
            row = "".join(f"<{tag}>{c}</{tag}>" for c in cells)
            html_lines.append(f"<tr>{row}</tr>")
        else:
            if in_table:
                html_lines.append("</table>")
                in_table = False
            # Bold
            line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            # Italic
            line = re.sub(r"_(.+?)_", r"<em>\1</em>", line)
            # List items
            if line.startswith("- "):
                line = f"<li>{line[2:]}</li>"
            elif line.startswith("  > "):
                line = f"<blockquote>{line[4:]}</blockquote>"
            elif line.strip():
                line = f"<p>{line}</p>"
            html_lines.append(line)

    if in_table:
        html_lines.append("</table>")

    return "\n".join(html_lines)
