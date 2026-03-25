"""F3: Ingestion Pipeline - Dokumente registrieren und verknuepfen."""

import hashlib
import uuid
from pathlib import Path

from sqlalchemy import select

from ngdai.core.config import get_settings, PROJECT_ROOT
from ngdai.db.engine import get_session
from ngdai.db.models import DocumentModel, DocumentEntityModel
from ngdai.definitions.service import find_directory_definition_for_path
from ngdai.entities.service import detect_entity_from_text, parse_aktenzeichen


def ingest_path(path: str) -> dict:
    """Importiert eine Datei oder alle TXT-Dateien in einem Verzeichnis.

    Args:
        path: Datei- oder Verzeichnispfad.

    Returns:
        Dict mit 'ingested' und 'skipped' counts.
    """
    p = Path(path)
    if p.is_file():
        files = [p]
    elif p.is_dir():
        files = sorted(p.rglob("*.txt"))
    else:
        raise FileNotFoundError(f"Pfad nicht gefunden: {path}")

    ingested = 0
    skipped = 0

    for file_path in files:
        result = _ingest_single_file(file_path)
        if result:
            ingested += 1
        else:
            skipped += 1

    return {"ingested": ingested, "skipped": skipped}


def _ingest_single_file(file_path: Path) -> bool:
    """Importiert eine einzelne TXT-Datei.

    Returns:
        True wenn erfolgreich importiert, False wenn uebersprungen.
    """
    session = get_session()
    try:
        # Prüfe ob Datei bereits importiert
        rel_path = _relative_path(file_path)
        existing = session.execute(
            select(DocumentModel).where(DocumentModel.file_path == rel_path)
        ).scalar_one_or_none()

        if existing:
            return False  # Bereits importiert

        # Datei lesen
        text = _read_text_file(file_path)
        if not text:
            return False

        # Hash berechnen
        file_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        # Directory Definition finden
        dir_def = find_directory_definition_for_path(rel_path)

        # Dokument erstellen
        doc_id = str(uuid.uuid4())
        doc = DocumentModel(
            id=doc_id,
            file_path=rel_path,
            original_filename=file_path.name,
            document_type=dir_def.document_type if dir_def else _guess_document_type(rel_path),
            sector=dir_def.sector if dir_def else _guess_sector(rel_path),
            regulatory_period=dir_def.regulatory_period if dir_def else "",
            ingestion_status="ingested",
            file_hash_sha256=file_hash,
            char_count=len(text),
            definition_id=dir_def.id if dir_def else None,
        )
        session.add(doc)

        # Entity-Erkennung aus Text
        _link_entities(session, doc_id, text)

        session.commit()
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _link_entities(session, doc_id: str, text: str) -> None:
    """Verknuepft erkannte Entities mit dem Dokument."""
    try:
        detected = detect_entity_from_text(text, threshold=82)
        for entity, score, az in detected:
            link = DocumentEntityModel(
                document_id=doc_id,
                entity_id=entity.id,
                association_type="auto_detected",
                confidence=score / 100.0,
            )
            session.add(link)
    except Exception:
        # Entity-Erkennung ist optional, Ingestion soll nicht fehlschlagen
        pass


def _read_text_file(file_path: Path) -> str | None:
    """Liest eine TXT-Datei mit Encoding-Fallback."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return file_path.read_text(encoding=encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


def _relative_path(file_path: Path) -> str:
    """Erzeugt einen relativen Pfad zum Projekt-Root."""
    try:
        return str(file_path.resolve().relative_to(PROJECT_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(file_path).replace("\\", "/")


def _guess_document_type(path: str) -> str:
    """Rät den Dokumenttyp anhand des Pfads."""
    path_lower = path.lower()
    if "eog" in path_lower:
        return "eog"
    if "geschaeftsbericht" in path_lower or "geschäftsbericht" in path_lower or "gb" in path_lower:
        return "geschaeftsbericht"
    if "festlegung" in path_lower:
        return "festlegung"
    if "preisblat" in path_lower or "preisblät" in path_lower:
        return "preisblatt"
    return "unknown"


def _guess_sector(path: str) -> str:
    """Rät den Sektor anhand des Pfads."""
    path_lower = path.lower()
    if "bk8" in path_lower or "strom" in path_lower:
        return "strom"
    if "bk9" in path_lower or "gas" in path_lower:
        return "gas"
    return ""


def get_document(doc_id: str) -> DocumentModel | None:
    """Holt ein Dokument per ID."""
    session = get_session()
    try:
        return session.get(DocumentModel, doc_id)
    finally:
        session.close()


def list_documents(
    document_type: str | None = None,
    sector: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[DocumentModel]:
    """Listet Dokumente mit optionalen Filtern."""
    session = get_session()
    try:
        stmt = select(DocumentModel)
        if document_type:
            stmt = stmt.where(DocumentModel.document_type == document_type)
        if sector:
            stmt = stmt.where(DocumentModel.sector == sector)
        if status:
            stmt = stmt.where(DocumentModel.ingestion_status == status)
        stmt = stmt.order_by(DocumentModel.file_path).limit(limit).offset(offset)
        return list(session.execute(stmt).scalars().all())
    finally:
        session.close()


def count_documents(status: str | None = None) -> int:
    """Zählt Dokumente."""
    from sqlalchemy import func
    session = get_session()
    try:
        stmt = select(func.count(DocumentModel.id))
        if status:
            stmt = stmt.where(DocumentModel.ingestion_status == status)
        return session.execute(stmt).scalar_one()
    finally:
        session.close()


def get_document_text(doc_id: str) -> str | None:
    """Liest den Volltext eines Dokuments von der Festplatte."""
    doc = get_document(doc_id)
    if not doc:
        return None

    file_path = PROJECT_ROOT / doc.file_path
    if not file_path.exists():
        return None

    return _read_text_file(file_path)
