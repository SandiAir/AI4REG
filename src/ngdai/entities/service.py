"""F1: Legal Entity Management - Import, CRUD, Fuzzy-Matching."""

import csv
import re
import uuid
from pathlib import Path

from rapidfuzz import fuzz, process
from sqlalchemy import select

from ngdai.db.engine import get_session
from ngdai.db.models import LegalEntityModel


# ── CSV Import ─────────────────────────────────────────────

# Mapping: CSV-Spalte → DB-Feld
_CSV_FIELD_MAP = {
    "MaStR-Nr.": "mastr_nr",
    "Name des Marktakteurs": "name",
    "Marktrollen": "roles",
    "Bundesland": "state",
    "Postleitzahl": "zip_code",
    "Ort": "city",
    "ACER-Code": "acer_code",
    "Tätigkeitsstatus": "status",
}


def import_marktakteure_csv(csv_path: str, sector: str) -> int:
    """Importiert Marktakteure aus einer MaStR-CSV-Datei.

    Args:
        csv_path: Pfad zur CSV-Datei (Semikolon-getrennt, UTF-8-BOM).
        sector: 'strom' oder 'gas'.

    Returns:
        Anzahl importierter/aktualisierter Entities.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV nicht gefunden: {csv_path}")

    # BOM-tolerantes Lesen
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        rows = list(reader)

    session = get_session()
    count = 0
    try:
        for row in rows:
            mastr_nr = row.get("MaStR-Nr.", "").strip()
            if not mastr_nr:
                continue

            name = row.get("Name des Marktakteurs", "").strip()
            if not name:
                continue

            # Rollen: kommasepariert → Liste
            roles_raw = row.get("Marktrollen", "")
            roles = [r.strip() for r in roles_raw.split(",") if r.strip()]

            # Prüfe ob Entity mit gleicher MaStR-Nr. existiert
            existing = session.execute(
                select(LegalEntityModel).where(LegalEntityModel.mastr_nr == mastr_nr)
            ).scalar_one_or_none()

            if existing:
                # Update
                existing.name = name
                existing.state = row.get("Bundesland", "").strip()
                existing.city = row.get("Ort", "").strip()
                existing.zip_code = row.get("Postleitzahl", "").strip()
                existing.roles = roles
                existing.acer_code = row.get("ACER-Code", "").strip()
                existing.status = row.get("Tätigkeitsstatus", "").strip()
                # Sektor ergänzen falls nicht vorhanden
                if sector not in (existing.sectors or []):
                    existing.sectors = (existing.sectors or []) + [sector]
            else:
                entity = LegalEntityModel(
                    id=str(uuid.uuid4()),
                    mastr_nr=mastr_nr,
                    name=name,
                    sectors=[sector],
                    state=row.get("Bundesland", "").strip(),
                    city=row.get("Ort", "").strip(),
                    zip_code=row.get("Postleitzahl", "").strip(),
                    roles=roles,
                    acer_code=row.get("ACER-Code", "").strip(),
                    status=row.get("Tätigkeitsstatus", "").strip(),
                    extra_data={
                        "strasse": row.get("Straße", "").strip(),
                        "hausnummer": row.get("Hausnummer", "").strip(),
                        "land": row.get("Land", "").strip(),
                        "marktfunktion": row.get("Marktfunktion", "").strip(),
                        "registrierungsdatum": row.get("Registrierungsdatum", "").strip(),
                    },
                )
                session.add(entity)
            count += 1

        session.commit()
    finally:
        session.close()

    return count


# ── Entity Lookup ──────────────────────────────────────────

def get_entity(entity_id: str) -> LegalEntityModel | None:
    """Holt eine Entity per ID."""
    session = get_session()
    try:
        return session.get(LegalEntityModel, entity_id)
    finally:
        session.close()


def get_entity_by_mastr(mastr_nr: str) -> LegalEntityModel | None:
    """Holt eine Entity per MaStR-Nummer."""
    session = get_session()
    try:
        return session.execute(
            select(LegalEntityModel).where(LegalEntityModel.mastr_nr == mastr_nr)
        ).scalar_one_or_none()
    finally:
        session.close()


def list_entities(
    sector: str | None = None,
    state: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[LegalEntityModel]:
    """Listet Entities mit optionalen Filtern."""
    session = get_session()
    try:
        stmt = select(LegalEntityModel)
        if sector:
            stmt = stmt.where(LegalEntityModel.sectors.contains([sector]))
        if state:
            stmt = stmt.where(LegalEntityModel.state == state)
        stmt = stmt.order_by(LegalEntityModel.name).limit(limit).offset(offset)
        return list(session.execute(stmt).scalars().all())
    finally:
        session.close()


def count_entities(sector: str | None = None) -> int:
    """Zählt Entities."""
    session = get_session()
    try:
        from sqlalchemy import func
        stmt = select(func.count(LegalEntityModel.id))
        if sector:
            stmt = stmt.where(LegalEntityModel.sectors.contains([sector]))
        return session.execute(stmt).scalar_one()
    finally:
        session.close()


# ── Fuzzy Matching ─────────────────────────────────────────

# In-Memory-Cache für schnelles Matching
_entity_names_cache: dict[str, str] | None = None


def _build_name_cache() -> dict[str, str]:
    """Baut den Name→ID Cache (einmalig pro Session)."""
    global _entity_names_cache
    if _entity_names_cache is not None:
        return _entity_names_cache

    session = get_session()
    try:
        entities = session.execute(
            select(LegalEntityModel.id, LegalEntityModel.name)
        ).all()
        _entity_names_cache = {name: eid for eid, name in entities}
        return _entity_names_cache
    finally:
        session.close()


def invalidate_name_cache() -> None:
    """Cache invalidieren (nach Import aufrufen)."""
    global _entity_names_cache
    _entity_names_cache = None


def find_entity_by_name(
    name: str,
    threshold: int = 80,
    limit: int = 5,
) -> list[tuple[LegalEntityModel, float]]:
    """Findet Entities per Fuzzy-Matching auf den Namen.

    Args:
        name: Suchbegriff.
        threshold: Mindest-Score (0-100).
        limit: Maximale Anzahl Ergebnisse.

    Returns:
        Liste von (Entity, Score) Tupeln, absteigend sortiert.
    """
    name_cache = _build_name_cache()
    if not name_cache:
        return []

    # rapidfuzz: WRatio für robustes Matching (Teilstrings, Wortumstellungen)
    matches = process.extract(
        name,
        name_cache.keys(),
        scorer=fuzz.WRatio,
        limit=limit,
        score_cutoff=threshold,
    )

    if not matches:
        return []

    session = get_session()
    try:
        results = []
        for match_name, score, _ in matches:
            entity_id = name_cache[match_name]
            entity = session.get(LegalEntityModel, entity_id)
            if entity:
                results.append((entity, score))
        return results
    finally:
        session.close()


# ── Aktenzeichen-Parser ───────────────────────────────────

# BK8-xx-xxxxx (Strom) oder BK9-xx-xxxxx (Gas)
_AZ_PATTERN = re.compile(r"BK[489]\s*[-–]\s*\d{2}\s*[-–]\s*\d{3,5}")

# Aus Aktenzeichen den Netzbetreiber-Namen extrahieren:
# Typisches Format in EOG-Beschlüssen: "BK8-21-00148 - Stadtwerke Elmshorn GmbH"
_AZ_WITH_NAME_PATTERN = re.compile(
    r"BK[489]\s*[-–]\s*\d{2}\s*[-–]\s*\d{3,5}\s*[-–]\s*(.+?)(?:\n|$)"
)


def parse_aktenzeichen(text: str) -> list[str]:
    """Extrahiert Aktenzeichen aus einem Text.

    Returns:
        Liste der gefundenen Aktenzeichen (normalisiert).
    """
    matches = _AZ_PATTERN.findall(text[:5000])  # Nur Anfang durchsuchen
    # Normalisieren: einheitliche Bindestriche, keine Leerzeichen
    normalized = []
    for m in matches:
        az = re.sub(r"\s*[-–]\s*", "-", m)
        if az not in normalized:
            normalized.append(az)
    return normalized


def detect_entity_from_text(
    text: str,
    threshold: int = 85,
) -> list[tuple[LegalEntityModel, float, str]]:
    """Versucht Entities aus Dokumenttext zu erkennen.

    Strategie:
    1. Aktenzeichen mit Name parsen (z.B. "BK8-21-00148 - Stadtwerke Elmshorn")
    2. Falls Name gefunden: Fuzzy-Match gegen Entity-DB

    Returns:
        Liste von (Entity, Score, Aktenzeichen) Tupeln.
    """
    results = []
    seen_entities = set()

    # Strategie 1: Aktenzeichen + Name
    for match in _AZ_WITH_NAME_PATTERN.finditer(text[:10000]):
        name_part = match.group(1).strip()
        az = parse_aktenzeichen(match.group(0))
        az_str = az[0] if az else ""

        # Name bereinigen: häufige Suffixe entfernen
        name_clean = re.sub(r"\s*(GmbH|AG|KG|e\.G\.|eG|mbH)\s*$", "", name_part).strip()
        if len(name_clean) < 3:
            continue

        matches = find_entity_by_name(name_clean, threshold=threshold, limit=1)
        if matches:
            entity, score = matches[0]
            if entity.id not in seen_entities:
                results.append((entity, score, az_str))
                seen_entities.add(entity.id)

    return results
