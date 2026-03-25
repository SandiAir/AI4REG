"""FastAPI Application - Haupteinstiegspunkt fuer den Web-Server."""

from pathlib import Path

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
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


# ── Dashboard ──────────────────────────────────────────────

@app.get("/")
def dashboard(request: Request):
    """Dashboard mit Live-Stats via HTMX."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


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
    return templates.TemplateResponse("entities.html", {"request": request})


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
    return templates.TemplateResponse("entity_detail.html", {
        "request": request,
        "entity": entity,
    })


# ── Documents ──────────────────────────────────────────────

@app.get("/documents")
def documents_page(request: Request):
    return templates.TemplateResponse("documents.html", {"request": request})


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
    return templates.TemplateResponse("query.html", {"request": request, "q": q})


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
