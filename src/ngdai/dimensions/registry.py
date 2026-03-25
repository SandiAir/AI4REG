"""Dimensions-Registry: Laedt DimensionTypes aus YAML in die DB."""

from pathlib import Path

import yaml

from ngdai.core.config import CONFIG_PATH
from ngdai.db.engine import get_session
from ngdai.db.models import DimensionTypeModel


DIMENSION_TYPES_PATH = CONFIG_PATH / "dimensions" / "dimension_types.yaml"


def load_dimension_types() -> int:
    """Laedt alle Dimensionstypen aus der YAML-Datei in die DB.

    Returns:
        Anzahl geladener Typen.
    """
    if not DIMENSION_TYPES_PATH.exists():
        return 0

    with open(DIMENSION_TYPES_PATH, "r", encoding="utf-8") as f:
        types_data = yaml.safe_load(f)

    session = get_session()
    count = 0
    try:
        for dt in types_data:
            existing = session.get(DimensionTypeModel, dt["id"])
            if existing:
                # Update
                existing.name = dt["name"]
                existing.description = dt.get("description", "")
                existing.attributes_schema = dt.get("attributes_schema", {})
                existing.attribution_sources = dt.get("attribution_sources", [])
                existing.ordinal = dt.get("ordinal", False)
                existing.hierarchical = dt.get("hierarchical", False)
            else:
                # Insert
                model = DimensionTypeModel(
                    id=dt["id"],
                    name=dt["name"],
                    description=dt.get("description", ""),
                    attributes_schema=dt.get("attributes_schema", {}),
                    attribution_sources=dt.get("attribution_sources", []),
                    ordinal=dt.get("ordinal", False),
                    hierarchical=dt.get("hierarchical", False),
                )
                session.add(model)
            count += 1
        session.commit()
    finally:
        session.close()

    return count


def get_dimension_type(type_id: str) -> DimensionTypeModel | None:
    """Holt einen DimensionType aus der DB."""
    session = get_session()
    try:
        return session.get(DimensionTypeModel, type_id)
    finally:
        session.close()


def list_dimension_types() -> list[DimensionTypeModel]:
    """Listet alle DimensionTypes."""
    session = get_session()
    try:
        return session.query(DimensionTypeModel).order_by(DimensionTypeModel.name).all()
    finally:
        session.close()
