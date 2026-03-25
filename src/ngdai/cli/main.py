"""ngdai CLI - Haupteinstiegspunkt."""

import typer
from rich.console import Console

app = typer.Typer(
    name="ngdai",
    help="Wissensbasierte Analyseplattform fuer die deutsche Netzentgeltregulierung",
    no_args_is_help=True,
)
console = Console()


# ── Admin Commands ──────────────────────────────────────────

@app.command()
def init():
    """Datenbank initialisieren und Grunddaten laden."""
    from ngdai.db.engine import get_engine
    from ngdai.db.models import Base

    console.print("[bold blue]ngdai init[/bold blue] - Datenbank initialisieren...")

    engine = get_engine()
    Base.metadata.create_all(engine)
    console.print("[green]Tabellen erstellt.[/green]")

    # Dimension Types laden
    from ngdai.dimensions.registry import load_dimension_types
    count = load_dimension_types()
    console.print(f"[green]{count} Dimensionstypen geladen.[/green]")

    # Fact Definitions laden
    from ngdai.definitions.service import load_fact_definitions, load_directory_definitions
    count = load_fact_definitions()
    console.print(f"[green]{count} Fakt-Definitionen geladen.[/green]")

    # Directory Definitions laden
    count = load_directory_definitions()
    console.print(f"[green]{count} Verzeichnis-Definitionen geladen.[/green]")

    console.print("[bold green]Initialisierung abgeschlossen.[/bold green]")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host"),
    port: int = typer.Option(None, help="Port (default: PORT env oder 8000)"),
):
    """FastAPI-Server starten."""
    import uvicorn
    from ngdai.core.config import get_settings

    settings = get_settings()
    actual_port = port if port is not None else settings.get_port()
    is_dev = settings.env == "development"

    console.print(f"[bold blue]ngdai serve[/bold blue] - Server starten auf {host}:{actual_port}...")
    uvicorn.run("ngdai.api.app:app", host=host, port=actual_port, reload=is_dev)


# ── Import Commands ─────────────────────────────────────────

@app.command(name="import-marktakteure")
def import_marktakteure(
    csv_path: str = typer.Argument(help="Pfad zur Marktakteure-CSV"),
    sector: str = typer.Option(..., help="Sektor: strom oder gas"),
):
    """Marktakteure aus MaStR-CSV importieren."""
    from ngdai.entities.service import import_marktakteure_csv, invalidate_name_cache
    count = import_marktakteure_csv(csv_path, sector)
    invalidate_name_cache()
    console.print(f"[green]{count} Marktakteure ({sector}) importiert.[/green]")


# ── Ingestion Commands ──────────────────────────────────────

@app.command()
def ingest(
    path: str = typer.Argument(help="Datei oder Verzeichnis zum Importieren"),
):
    """Dokumente importieren (Ingestion Pipeline)."""
    from ngdai.ingestion.service import ingest_path
    result = ingest_path(path)
    console.print(f"[green]{result['ingested']} Dokumente importiert, {result['skipped']} uebersprungen.[/green]")


# ── Extraction Commands ─────────────────────────────────────

@app.command()
def extract(
    document_id: str = typer.Argument(None, help="Dokument-ID (oder --all)"),
    all_pending: bool = typer.Option(False, "--all", help="Alle unverarbeiteten Dokumente extrahieren"),
):
    """Datenpunkte aus Dokumenten extrahieren."""
    from ngdai.extraction.service import extract_document, extract_all_pending
    if all_pending:
        result = extract_all_pending()
        console.print(f"[green]{result['extracted']} Dokumente extrahiert, {result['failed']} fehlgeschlagen.[/green]")
    elif document_id:
        result = extract_document(document_id)
        console.print(f"[green]{result['facts_count']} Fakten extrahiert aus {document_id}.[/green]")
    else:
        console.print("[red]Bitte Dokument-ID oder --all angeben.[/red]")


# ── Query Commands ──────────────────────────────────────────

@app.command()
def query(
    question: str = typer.Argument(help="Frage an das System"),
):
    """Frage an das Wissenssystem stellen."""
    from ngdai.query.service import execute_query
    result = execute_query(question)
    console.print(result)


if __name__ == "__main__":
    app()
