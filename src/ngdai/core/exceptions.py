"""Zentrale Exceptions fuer ngdai."""


class NgdaiError(Exception):
    """Basis-Exception fuer alle ngdai-Fehler."""


class ConfigurationError(NgdaiError):
    """Konfigurationsfehler."""


class DefinitionNotFoundError(NgdaiError):
    """Verzeichnis-Definition nicht gefunden."""


class EntityNotFoundError(NgdaiError):
    """Legal Entity nicht gefunden."""


class DocumentNotFoundError(NgdaiError):
    """Dokument nicht gefunden."""


class ExtractionError(NgdaiError):
    """Fehler bei der Extraktion."""


class ValidationError(NgdaiError):
    """Validierungsfehler (Daten, Schema, etc.)."""


class GraphError(NgdaiError):
    """Fehler bei Knowledge-Graph-Operationen."""


class LLMError(NgdaiError):
    """Fehler bei LLM-Aufrufen."""


class IngestionError(NgdaiError):
    """Fehler bei der Dokumenten-Ingestion."""
