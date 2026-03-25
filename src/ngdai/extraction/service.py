"""F4: Closed Extraction - LLM-basierte Faktenextraktion."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select

from ngdai.core.config import get_settings, PROJECT_ROOT
from ngdai.core.exceptions import ExtractionError
from ngdai.db.engine import get_session
from ngdai.db.models import (
    DocumentModel,
    ExtractionRunModel,
    FactModel,
    FactDimensionModel,
    DimensionInstanceModel,
)
from ngdai.extraction.prompts import get_prompt_for_document_type
from ngdai.ingestion.service import get_document_text
from ngdai.llm.client import extract_structured


# Maximale Zeichenlaenge fuer ein einzelnes LLM-Window
MAX_WINDOW_CHARS = 600_000  # ~150K Tokens bei 4 chars/token
OVERLAP_CHARS = 8_000       # ~2 Seiten Overlap


def extract_document(document_id: str) -> dict:
    """Extrahiert Fakten aus einem einzelnen Dokument.

    Returns:
        Dict mit 'facts_count' und 'extraction_run_id'.
    """
    session = get_session()
    try:
        doc = session.get(DocumentModel, document_id)
        if not doc:
            raise ExtractionError(f"Dokument nicht gefunden: {document_id}")

        if doc.document_type not in ("eog", "geschaeftsbericht"):
            raise ExtractionError(f"Keine Extraktion fuer Dokumenttyp '{doc.document_type}'")

        # Volltext laden
        text = get_document_text(document_id)
        if not text:
            raise ExtractionError(f"Kein Text fuer Dokument: {document_id}")

        # Prompts holen
        system_prompt, user_prompt = get_prompt_for_document_type(doc.document_type)

        # Extraction Run erstellen
        run_id = str(uuid.uuid4())
        run = ExtractionRunModel(
            id=run_id,
            document_id=document_id,
            extraction_type="closed",
            model_id=get_settings().llm.extraction_model,
            prompt_version="v1",
            status="running",
            started_at=datetime.now(),
        )
        session.add(run)
        session.commit()

        try:
            # Sliding Window falls noetig
            if len(text) > MAX_WINDOW_CHARS:
                all_results = _extract_with_sliding_window(text, system_prompt, user_prompt)
            else:
                all_results = [extract_structured(text, system_prompt, user_prompt)]

            # Doppelextraktion (2. Durchlauf zum Vergleich)
            settings = get_settings()
            if settings.extraction.double_extraction and len(text) <= MAX_WINDOW_CHARS:
                second_result = extract_structured(text, system_prompt, user_prompt)
                all_results.append(second_result)

            # Fakten aus Ergebnissen zusammenfuehren
            facts_count = _process_extraction_results(
                session, document_id, run_id, doc.document_type, all_results
            )

            # Run als erfolgreich markieren
            run = session.get(ExtractionRunModel, run_id)
            run.status = "completed"
            run.completed_at = datetime.now()

            # Dokument-Status updaten
            doc = session.get(DocumentModel, document_id)
            doc.ingestion_status = "extracted"

            session.commit()
            return {"facts_count": facts_count, "extraction_run_id": run_id}

        except Exception as e:
            run = session.get(ExtractionRunModel, run_id)
            run.status = "failed"
            run.extra_data = {"error": str(e)}
            run.completed_at = datetime.now()
            session.commit()
            raise ExtractionError(f"Extraktion fehlgeschlagen: {e}") from e

    finally:
        session.close()


def extract_all_pending() -> dict:
    """Extrahiert Fakten aus allen noch nicht extrahierten Dokumenten.

    Returns:
        Dict mit 'extracted' und 'failed' counts.
    """
    session = get_session()
    try:
        docs = session.execute(
            select(DocumentModel).where(
                DocumentModel.ingestion_status == "ingested",
                DocumentModel.document_type.in_(["eog", "geschaeftsbericht"]),
            )
        ).scalars().all()
        doc_ids = [d.id for d in docs]
    finally:
        session.close()

    extracted = 0
    failed = 0
    for doc_id in doc_ids:
        try:
            extract_document(doc_id)
            extracted += 1
        except ExtractionError:
            failed += 1

    return {"extracted": extracted, "failed": failed}


# ── Sliding Window ─────────────────────────────────────────

def _extract_with_sliding_window(
    text: str,
    system_prompt: str,
    user_prompt: str,
) -> list[dict]:
    """Extrahiert in Fenstern mit Overlap."""
    windows = []
    start = 0
    while start < len(text):
        end = start + MAX_WINDOW_CHARS
        windows.append(text[start:end])
        start = end - OVERLAP_CHARS
        if end >= len(text):
            break

    results = []
    for window_text in windows:
        result = extract_structured(window_text, system_prompt, user_prompt)
        results.append(result)

    return results


# ── Ergebnis-Verarbeitung ─────────────────────────────────

def _process_extraction_results(
    session,
    document_id: str,
    run_id: str,
    doc_type: str,
    results: list[dict],
) -> int:
    """Verarbeitet LLM-Ergebnisse und speichert Fakten in der DB.

    Bei mehreren Ergebnissen (Doppelextraktion/Windows): Deduplizierung
    mit hoechstem Confidence-Wert.
    """
    # Fakten sammeln und deduplizieren
    best_facts: dict[str, dict] = {}  # key: definition_id (+ jahr bei eog_jahr)

    for result in results:
        # Standard-Fakten
        for fact_data in result.get("fakten", []):
            fact_id = fact_data.get("id", "")
            if not fact_id:
                continue

            key = fact_id
            confidence = fact_data.get("confidence", 0.5)

            if key not in best_facts or confidence > best_facts[key].get("confidence", 0):
                best_facts[key] = fact_data

        # EOG-Jahreswerte (spezielle Behandlung)
        for jw in result.get("eog_jahreswerte", []):
            jahr = jw.get("jahr")
            if not jahr:
                continue
            key = f"eog_jahr_{jahr}"
            best_facts[key] = {
                "id": "eog_jahr",
                "value": jw.get("betrag"),
                "unit": "EUR",
                "source_text": jw.get("source_text", ""),
                "confidence": 0.9,
                "extra": {"jahr": jahr},
            }

    # Fakten in DB schreiben
    count = 0
    for key, fact_data in best_facts.items():
        value = fact_data.get("value")
        if value is None:
            continue

        fact = FactModel(
            id=str(uuid.uuid4()),
            definition_id=fact_data["id"],
            document_id=document_id,
            extraction_run_id=run_id,
            value=str(value),
            value_numeric=_to_float(value),
            unit=fact_data.get("unit", ""),
            confidence=fact_data.get("confidence", 0.5),
            source_text=fact_data.get("source_text", "")[:500],
            extra_data=fact_data.get("extra", {}),
        )
        session.add(fact)
        count += 1

    return count


def _to_float(value: Any) -> float | None:
    """Konvertiert Werte zu float, None bei Fehler."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            # Deutsche Notation: Punkt als Tausender, Komma als Dezimal
            cleaned = value.replace(".", "").replace(",", ".")
            return float(cleaned)
        except ValueError:
            return None
    return None
