"""F10: Directory Definitions + Fact Definitions Service."""

from pathlib import Path

import yaml

from ngdai.core.config import CONFIG_PATH
from ngdai.db.engine import get_session
from ngdai.db.models import FactDefinitionModel


FACT_DEFINITIONS_PATH = CONFIG_PATH / "ontology" / "fact_definitions.yaml"


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
