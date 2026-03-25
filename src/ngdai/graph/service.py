"""F5: Knowledge Graph - Facts als Graph-Knoten verwalten."""

from sqlalchemy import select, func

from ngdai.db.engine import get_session, cypher_query, init_age
from ngdai.db.models import (
    FactModel,
    FactDimensionModel,
    DimensionInstanceModel,
)


def ensure_graph_schema(session) -> None:
    """Stellt sicher, dass der Graph und grundlegende Labels existieren."""
    init_age(session)
    # AGE erstellt Labels automatisch beim ersten CREATE


def insert_fact_into_graph(session, fact_id: str) -> None:
    """Fuegt einen Fakt als Knoten in den AGE-Graphen ein.

    Erstellt:
    - Fact-Knoten mit Eigenschaften
    - IN_DIMENSION-Kanten zu allen verknuepften Dimensionsinstanzen
    """
    fact = session.get(FactModel, fact_id)
    if not fact:
        return

    # Fact-Knoten erstellen
    cypher_query(session, f"""
        MERGE (f:Fact {{id: '{fact.id}'}})
        SET f.definition_id = '{fact.definition_id}',
            f.document_id = '{fact.document_id}',
            f.value = '{fact.value}',
            f.confidence = {fact.confidence}
    """)

    # IN_DIMENSION-Kanten
    dims = session.execute(
        select(FactDimensionModel).where(FactDimensionModel.fact_id == fact_id)
    ).scalars().all()

    for fd in dims:
        dim_inst = session.get(DimensionInstanceModel, fd.dimension_instance_id)
        if dim_inst:
            cypher_query(session, f"""
                MATCH (f:Fact {{id: '{fact_id}'}})
                MERGE (d:DimensionInstance {{id: '{dim_inst.id}'}})
                SET d.name = '{_escape(dim_inst.name)}',
                    d.type_id = '{dim_inst.type_id}'
                MERGE (f)-[:IN_DIMENSION {{method: '{fd.attribution_method}', confidence: {fd.confidence}}}]->(d)
            """)


def build_graph_from_db() -> int:
    """Baut den kompletten Graphen aus allen Facts in der DB auf.

    Returns:
        Anzahl eingefuegter Fact-Knoten.
    """
    session = get_session()
    try:
        ensure_graph_schema(session)

        facts = session.execute(select(FactModel.id)).scalars().all()
        for fact_id in facts:
            insert_fact_into_graph(session, fact_id)

        session.commit()
        return len(facts)
    finally:
        session.close()


def query_facts_by_dimensions(
    dimension_filters: dict[str, str],
    definition_id: str | None = None,
) -> list[dict]:
    """Findet Facts die in bestimmten Dimensionen liegen.

    Args:
        dimension_filters: Dict von dimension_type_id → dimension_instance_name
            z.B. {"legal_entity": "Stadtwerke Elmshorn", "regulatory_period": "4.RP"}
        definition_id: Optional - nur Facts eines bestimmten Typs.

    Returns:
        Liste von Fact-Dicts mit Wert und Quellen.
    """
    session = get_session()
    try:
        # Relational query (zuverlaessiger als Cypher fuer einfache Lookups)
        stmt = select(FactModel)

        if definition_id:
            stmt = stmt.where(FactModel.definition_id == definition_id)

        # Join ueber FactDimension → DimensionInstance
        for dim_type_id, dim_value in dimension_filters.items():
            dim_alias = f"fd_{dim_type_id}"
            stmt = stmt.join(
                FactDimensionModel,
                FactModel.id == FactDimensionModel.fact_id,
            ).join(
                DimensionInstanceModel,
                FactDimensionModel.dimension_instance_id == DimensionInstanceModel.id,
            ).where(
                DimensionInstanceModel.type_id == dim_type_id,
                DimensionInstanceModel.name.ilike(f"%{dim_value}%"),
            )

        results = session.execute(stmt).scalars().all()
        return [_fact_to_dict(f) for f in results]
    finally:
        session.close()


def get_facts_for_entity(entity_name: str, definition_id: str | None = None) -> list[dict]:
    """Holt alle Facts fuer eine Entity (per Name, fuzzy)."""
    return query_facts_by_dimensions(
        dimension_filters={"legal_entity": entity_name},
        definition_id=definition_id,
    )


def get_facts_for_document(document_id: str) -> list[dict]:
    """Holt alle Facts eines Dokuments."""
    session = get_session()
    try:
        facts = session.execute(
            select(FactModel).where(FactModel.document_id == document_id)
        ).scalars().all()
        return [_fact_to_dict(f) for f in facts]
    finally:
        session.close()


def aggregate_facts(
    definition_id: str,
    dimension_filters: dict[str, str] | None = None,
) -> dict:
    """Berechnet Aggregationen ueber Facts eines Typs.

    Returns:
        Dict mit count, avg, min, max, median.
    """
    session = get_session()
    try:
        stmt = select(FactModel.value_numeric).where(
            FactModel.definition_id == definition_id,
            FactModel.value_numeric.isnot(None),
        )

        if dimension_filters:
            for dim_type_id, dim_value in dimension_filters.items():
                stmt = stmt.join(
                    FactDimensionModel,
                    FactModel.id == FactDimensionModel.fact_id,
                ).join(
                    DimensionInstanceModel,
                    FactDimensionModel.dimension_instance_id == DimensionInstanceModel.id,
                ).where(
                    DimensionInstanceModel.type_id == dim_type_id,
                    DimensionInstanceModel.name.ilike(f"%{dim_value}%"),
                )

        values = [v for (v,) in session.execute(stmt).all() if v is not None]

        if not values:
            return {"count": 0, "avg": None, "min": None, "max": None, "median": None}

        values.sort()
        n = len(values)
        median = values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2

        return {
            "count": n,
            "avg": round(sum(values) / n, 2),
            "min": min(values),
            "max": max(values),
            "median": round(median, 2),
        }
    finally:
        session.close()


def _fact_to_dict(fact: FactModel) -> dict:
    """Konvertiert ein FactModel in ein serialisierbares Dict."""
    return {
        "id": fact.id,
        "definition_id": fact.definition_id,
        "document_id": fact.document_id,
        "value": fact.value,
        "value_numeric": fact.value_numeric,
        "unit": fact.unit,
        "confidence": fact.confidence,
        "source_text": fact.source_text,
    }


def _escape(text: str) -> str:
    """Escaped einfache Anführungszeichen fuer Cypher."""
    return text.replace("'", "\\'")
