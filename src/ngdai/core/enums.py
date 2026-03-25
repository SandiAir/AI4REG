"""Zentrale Enumerationen fuer ngdai."""

from enum import Enum


class Sector(str, Enum):
    """Energiesektor."""
    STROM = "strom"
    GAS = "gas"


class DocumentType(str, Enum):
    """Dokumenttypen im System."""
    EOG = "eog"                          # Erloesobergrenze-Beschluss
    KKAUF = "kkauf"                      # Kapitalkostenaufschlag
    REGKONTO = "regkonto"                # Regulierungskonto
    GESCHAEFTSBERICHT = "geschaeftsbericht"
    FESTLEGUNG = "festlegung"
    PREISBLATT = "preisblatt"
    GERICHTSURTEIL = "gerichtsurteil"
    PARAGRAPH_23B = "paragraph_23b"
    PARAGRAPH_23C = "paragraph_23c"


class TemporalBehavior(str, Enum):
    """Zeitliches Verhalten eines Datenpunkts."""
    PERIOD_FIXED = "period_fixed"        # Einmal pro Regulierungsperiode
    ANNUALLY_VARIABLE = "annually_variable"  # Jaehrlich variabel


class ValueType(str, Enum):
    """Wertetyp eines Fakts."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"
    TEMPORAL = "temporal"


class QualityFlag(str, Enum):
    """Qualitaetsbewertung der Dokumentkonvertierung."""
    GREEN = "green"    # Confidence >= 0.95
    YELLOW = "yellow"  # Confidence >= 0.80
    RED = "red"        # Confidence < 0.80


class IngestionStatus(str, Enum):
    """Status eines Dokuments in der Pipeline."""
    PENDING = "pending"
    INGESTED = "ingested"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    FAILED = "failed"


class AttributionMethod(str, Enum):
    """Wie eine Dimension einem Fakt zugewiesen wurde."""
    DIRECTORY_DEFINITION = "directory_definition"
    EXTRACTION = "extraction"
    ENRICHMENT = "enrichment"
    MANUAL = "manual"
