"""F10: Directory Definitions + Fact Definitions Service."""

from pathlib import Path

import yaml

from ngdai.core.config import CONFIG_PATH
from ngdai.db.engine import get_session
from ngdai.db.models import DirectoryDefinitionModel, FactDefinitionModel


FACT_DEFINITIONS_PATH = CONFIG_PATH / "ontology" / "fact_definitions.yaml"
DIRECTORY_DEFINITIONS_PATH = CONFIG_PATH / "directories" / "definitions.yaml"


def load_fact_definitions() -> int:
    """Laedt alle Fakt-Definitionen aus YAML in die DB.

    Returns:
        Anzahl geladener Definitionen.
    """
    if not FACT_DEFINITIONS_PATH.exists():
        return 0

    with open(FACT_DEFINITIONS_PATH, "r", encoding="utf-8") as f:
        defs_data = yaml.safe_load(f)

    session = get_session()
    count = 0
    try:
        for fd in defs_data:
            existing = session.get(FactDefinitionModel, fd["id"])
            if existing:
                existing.name = fd["name"]
                existing.description = fd.get("description", "")
                existing.temporal_behavior = fd["temporal_behavior"]
                existing.applicable_sectors = fd.get("applicable_sectors", [])
                existing.value_type = fd.get("value_type", "numeric")
                existing.unit = fd.get("unit", "")
                existing.legal_basis = fd.get("legal_basis", "")
                existing.validation_rules = fd.get("validation_rules", {})
            else:
                model = FactDefinitionModel(
                    id=fd["id"],
                    name=fd["name"],
                    description=fd.get("description", ""),
                    temporal_behavior=fd["temporal_behavior"],
                    applicable_sectors=fd.get("applicable_sectors", []),
                    value_type=fd.get("value_type", "numeric"),
                    unit=fd.get("unit", ""),
                    legal_basis=fd.get("legal_basis", ""),
                    validation_rules=fd.get("validation_rules", {}),
                )
                session.add(model)
            count += 1
        session.commit()
    finally:
        session.close()

    return count


def list_fact_definitions() -> list[FactDefinitionModel]:
    """Listet alle Fakt-Definitionen."""
    session = get_session()
    try:
        return session.query(FactDefinitionModel).order_by(FactDefinitionModel.name).all()
    finally:
        session.close()


def get_fact_definition(definition_id: str) -> FactDefinitionModel | None:
    """Holt eine Fakt-Definition."""
    session = get_session()
    try:
        return session.get(FactDefinitionModel, definition_id)
    finally:
        session.close()


# ── Directory Definitions ──────────────────────────────────

def load_directory_definitions() -> int:
    """Laedt Directory-Definitionen aus YAML in die DB.

    Returns:
        Anzahl geladener Definitionen.
    """
    if not DIRECTORY_DEFINITIONS_PATH.exists():
        return 0

    with open(DIRECTORY_DEFINITIONS_PATH, "r", encoding="utf-8") as f:
        defs_data = yaml.safe_load(f)

    session = get_session()
    count = 0
    try:
        for dd in defs_data:
            existing = session.get(DirectoryDefinitionModel, dd["id"])
            if existing:
                existing.path = dd["path"]
                existing.document_type = dd["document_type"]
                existing.sector = dd["sector"]
                existing.regulatory_period = dd.get("regulatory_period", "")
                existing.period_start_year = dd.get("period_start_year")
                existing.period_end_year = dd.get("period_end_year")
                existing.source_authority = dd.get("source_authority", "")
                existing.source_reliability = dd.get("source_reliability", 0.9)
                existing.expected_period_fixed = dd.get("expected_period_fixed", [])
                existing.expected_annually_variable = dd.get("expected_annually_variable", [])
            else:
                model = DirectoryDefinitionModel(
                    id=dd["id"],
                    path=dd["path"],
                    document_type=dd["document_type"],
                    sector=dd["sector"],
                    regulatory_period=dd.get("regulatory_period", ""),
                    period_start_year=dd.get("period_start_year"),
                    period_end_year=dd.get("period_end_year"),
                    source_authority=dd.get("source_authority", ""),
                    source_reliability=dd.get("source_reliability", 0.9),
                    expected_period_fixed=dd.get("expected_period_fixed", []),
                    expected_annually_variable=dd.get("expected_annually_variable", []),
                )
                session.add(model)
            count += 1
        session.commit()
    finally:
        session.close()

    return count


def get_directory_definition(definition_id: str) -> DirectoryDefinitionModel | None:
    """Holt eine Directory-Definition per ID."""
    session = get_session()
    try:
        return session.get(DirectoryDefinitionModel, definition_id)
    finally:
        session.close()


def find_directory_definition_for_path(file_path: str) -> DirectoryDefinitionModel | None:
    """Findet die Directory-Definition fuer einen gegebenen Dateipfad.

    Matcht den laengsten uebereinstimmenden Pfad-Prefix.
    """
    from sqlalchemy import select

    session = get_session()
    try:
        all_defs = session.execute(
            select(DirectoryDefinitionModel).order_by(DirectoryDefinitionModel.path.desc())
        ).scalars().all()

        # Normalisiere Pfad-Separatoren
        normalized = file_path.replace("\\", "/")
        for dd in all_defs:
            dd_path = dd.path.replace("\\", "/")
            if dd_path in normalized:
                return dd
        return None
    finally:
        session.close()
