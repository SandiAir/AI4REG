"""F6: Query Engine - Strukturierte Abfragen gegen den Wissensgraphen."""

import re
from typing import Any

from ngdai.entities.service import find_entity_by_name, list_entities
from ngdai.graph.service import (
    get_facts_for_entity,
    aggregate_facts,
    query_facts_by_dimensions,
)


def execute_query(question: str) -> str:
    """Verarbeitet eine natuerlichsprachliche Frage und liefert eine formatierte Antwort.

    Phase 1: Regelbasiertes Query-Routing (kein LLM noetig).
    Phase 2: Intent-Klassifikation per LLM.

    Unterstuetzte Query-Typen:
    1. Entity-Fact-Query: "Effizienzwert Stadtwerke Elmshorn"
    2. Vergleich: "Stadtwerke Elmshorn vs Albwerk"
    3. Aggregation: "Median Effizienzwert 4.RP Strom"
    """
    question_lower = question.lower().strip()

    # Query-Routing
    if _is_comparison_query(question_lower):
        return _handle_comparison(question)
    elif _is_aggregation_query(question_lower):
        return _handle_aggregation(question)
    else:
        return _handle_entity_fact_query(question)


# ── Query-Typ-Erkennung ──────────────────────────────────

def _is_comparison_query(q: str) -> bool:
    return any(kw in q for kw in [" vs ", " vs. ", " gegen ", " vergleich ", " verglichen "])


def _is_aggregation_query(q: str) -> bool:
    return any(kw in q for kw in ["median", "durchschnitt", "mittelwert", "minimum", "maximum", "anzahl"])


# ── Entity-Fact Query ─────────────────────────────────────

def _handle_entity_fact_query(question: str) -> str:
    """Beantwortet Fragen wie 'Effizienzwert Stadtwerke Elmshorn'."""
    # Bekannte Fakt-Typen erkennen
    fact_type = _detect_fact_type(question)

    # Entity erkennen
    entity_name = _extract_entity_name(question, fact_type)
    if not entity_name:
        return f"Konnte keinen Netzbetreiber in der Frage erkennen: '{question}'"

    # Entity per Fuzzy-Match finden
    matches = find_entity_by_name(entity_name, threshold=70, limit=3)
    if not matches:
        return f"Kein Netzbetreiber gefunden fuer '{entity_name}'"

    entity, score = matches[0]

    # Facts holen
    facts = get_facts_for_entity(entity.name, definition_id=fact_type)

    if not facts:
        return (
            f"**{entity.name}** (Match: {score:.0f}%)\n"
            f"Keine {'Fakten' if not fact_type else fact_type}-Daten gefunden."
        )

    # Formatierung
    lines = [f"**{entity.name}** ({entity.state}, {', '.join(entity.sectors or [])})\n"]

    for fact in facts:
        value = fact["value"]
        unit = fact["unit"]
        conf = fact["confidence"]
        source = fact["source_text"][:100] if fact.get("source_text") else ""

        lines.append(f"- **{fact['definition_id']}**: {value} {unit} (Konfidenz: {conf:.0%})")
        if source:
            lines.append(f"  > _{source}_")

    return "\n".join(lines)


# ── Vergleich ─────────────────────────────────────────────

def _handle_comparison(question: str) -> str:
    """Beantwortet Vergleichsfragen wie 'Elmshorn vs Albwerk EOG 4.RP'."""
    # Entities extrahieren (durch vs/vs./gegen getrennt)
    parts = re.split(r"\s+(?:vs\.?|gegen|vergleich)\s+", question, flags=re.IGNORECASE)
    if len(parts) < 2:
        return "Vergleich braucht zwei Entities, getrennt durch 'vs'."

    entity_a_name = _clean_entity_part(parts[0])
    entity_b_name = _clean_entity_part(parts[1])

    fact_type = _detect_fact_type(question)

    matches_a = find_entity_by_name(entity_a_name, threshold=70, limit=1)
    matches_b = find_entity_by_name(entity_b_name, threshold=70, limit=1)

    if not matches_a:
        return f"Entity A nicht gefunden: '{entity_a_name}'"
    if not matches_b:
        return f"Entity B nicht gefunden: '{entity_b_name}'"

    entity_a = matches_a[0][0]
    entity_b = matches_b[0][0]

    facts_a = get_facts_for_entity(entity_a.name, definition_id=fact_type)
    facts_b = get_facts_for_entity(entity_b.name, definition_id=fact_type)

    # Tabelle bauen
    lines = [
        f"**Vergleich: {entity_a.name} vs. {entity_b.name}**\n",
        f"| Datenpunkt | {entity_a.name} | {entity_b.name} |",
        "|:-----------|:----------------|:----------------|",
    ]

    # Facts nach definition_id gruppieren
    a_by_def = {f["definition_id"]: f for f in facts_a}
    b_by_def = {f["definition_id"]: f for f in facts_b}
    all_defs = sorted(set(list(a_by_def.keys()) + list(b_by_def.keys())))

    for def_id in all_defs:
        val_a = f"{a_by_def[def_id]['value']} {a_by_def[def_id]['unit']}" if def_id in a_by_def else "—"
        val_b = f"{b_by_def[def_id]['value']} {b_by_def[def_id]['unit']}" if def_id in b_by_def else "—"
        lines.append(f"| {def_id} | {val_a} | {val_b} |")

    if not all_defs:
        lines.append("| (keine Daten) | — | — |")

    return "\n".join(lines)


# ── Aggregation ───────────────────────────────────────────

def _handle_aggregation(question: str) -> str:
    """Beantwortet Aggregationsfragen wie 'Median Effizienzwert 4.RP Strom'."""
    fact_type = _detect_fact_type(question)
    if not fact_type:
        return "Konnte keinen Datentyp in der Frage erkennen."

    # Dimensionsfilter erkennen
    dim_filters = {}
    q_lower = question.lower()

    if "4.rp" in q_lower or "4. regulierungsperiode" in q_lower or "vierte" in q_lower:
        dim_filters["regulatory_period"] = "4.RP"
    elif "3.rp" in q_lower or "3. regulierungsperiode" in q_lower or "dritte" in q_lower:
        dim_filters["regulatory_period"] = "3.RP"

    if "strom" in q_lower:
        dim_filters["sector"] = "strom"
    elif "gas" in q_lower:
        dim_filters["sector"] = "gas"

    result = aggregate_facts(fact_type, dimension_filters=dim_filters if dim_filters else None)

    if result["count"] == 0:
        return f"Keine Daten fuer {fact_type} mit den angegebenen Filtern."

    lines = [
        f"**Aggregation: {fact_type}**",
        f"Filter: {dim_filters or '(keine)'}",
        "",
        f"- Anzahl: {result['count']}",
        f"- Durchschnitt: {result['avg']}",
        f"- Median: {result['median']}",
        f"- Minimum: {result['min']}",
        f"- Maximum: {result['max']}",
    ]
    return "\n".join(lines)


# ── Hilfsfunktionen ───────────────────────────────────────

# Bekannte Fakt-IDs und ihre Synonyme
_FACT_SYNONYMS: dict[str, list[str]] = {
    "effizienzwert": ["effizienz", "effizienzwert", "benchmark", "effizienzbenchmark"],
    "ausgangsniveau": ["ausgangsniveau", "kostenniveau", "basiskosten"],
    "eog_jahr": ["eog", "erlosobergrenze", "erlösobergrenze", "erloesobergrenze"],
    "dnb_kosten": ["dnb", "nicht beeinflussbar", "dauerhaft nicht beeinflussbar"],
    "gb_umsatz": ["umsatz", "umsatzerloese", "umsatzerlöse", "revenue"],
    "gb_ebit": ["ebit", "betriebsergebnis"],
    "gb_mitarbeiter": ["mitarbeiter", "beschaeftigte", "beschäftigte"],
    "gb_investitionen": ["investition", "investitionen", "capex"],
    "gb_netzlaenge": ["netzlaenge", "netzlänge", "leitungslaenge"],
    "verfahrensart": ["verfahrensart", "vereinfacht", "regelverfahren"],
}


def _detect_fact_type(question: str) -> str | None:
    """Erkennt den Fakt-Typ aus einer natuerlichsprachlichen Frage."""
    q_lower = question.lower()
    for fact_id, synonyms in _FACT_SYNONYMS.items():
        for synonym in synonyms:
            if synonym in q_lower:
                return fact_id
    return None


def _extract_entity_name(question: str, fact_type: str | None) -> str | None:
    """Extrahiert den Entity-Namen aus der Frage.

    Entfernt bekannte Keywords (Fakt-Typ, Dimensionen) und nimmt den Rest.
    """
    # Keywords entfernen
    cleaned = question
    remove_words = [
        "effizienzwert", "ausgangsniveau", "eog", "erlosobergrenze", "erlösobergrenze",
        "dnb", "umsatz", "ebit", "mitarbeiter", "investitionen", "netzlaenge", "netzlänge",
        "4.rp", "3.rp", "strom", "gas", "vergleich",
        "median", "durchschnitt", "mittelwert", "minimum", "maximum",
        "was", "ist", "der", "die", "das", "von", "fuer", "für", "im", "in", "des",
    ]
    words = cleaned.split()
    remaining = [w for w in words if w.lower().strip("?.,!") not in remove_words]

    name = " ".join(remaining).strip()
    return name if len(name) >= 2 else None


def _clean_entity_part(text: str) -> str:
    """Bereinigt einen Entity-Teil aus einer Vergleichsfrage."""
    remove_words = [
        "eog", "effizienzwert", "4.rp", "3.rp", "strom", "gas",
        "ausgangsniveau", "vergleich",
    ]
    words = text.split()
    remaining = [w for w in words if w.lower().strip("?.,!") not in remove_words]
    return " ".join(remaining).strip()
