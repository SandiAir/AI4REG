"""Einfacher interner Event-Bus fuer lose Kopplung zwischen Modulen."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

# Event-Typen
FACTS_INSERTED = "facts_inserted"
DOCUMENT_INGESTED = "document_ingested"
ENTITY_CREATED = "entity_created"
DIMENSION_ATTRIBUTED = "dimension_attributed"

# Globaler Event-Bus (einfache Loesung fuer Monolith)
_handlers: dict[str, list[Callable]] = defaultdict(list)


def on(event_type: str, handler: Callable) -> None:
    """Registriert einen Handler fuer einen Event-Typ."""
    _handlers[event_type].append(handler)


def emit(event_type: str, **data: Any) -> None:
    """Feuert ein Event und ruft alle registrierten Handler auf."""
    for handler in _handlers.get(event_type, []):
        handler(**data)


def clear() -> None:
    """Entfernt alle Handler (fuer Tests)."""
    _handlers.clear()
