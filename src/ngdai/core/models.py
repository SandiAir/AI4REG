"""Zentrale Domain-Modelle (Pydantic) - unabhaengig von DB."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ngdai.core.enums import (
    AttributionMethod,
    DocumentType,
    IngestionStatus,
    QualityFlag,
    Sector,
    TemporalBehavior,
    ValueType,
)


def new_id() -> str:
    return str(uuid.uuid4())


# ── Dimensions ──────────────────────────────────────────────

class DimensionType(BaseModel):
    """Meta-Definition eines Dimensionstyps (aus YAML)."""
    id: str                              # z.B. 'legal_entity', 'proceeding'
    name: str                            # Anzeigename
    description: str = ""
    attributes_schema: dict[str, Any] = Field(default_factory=dict)
    attribution_sources: list[str] = Field(default_factory=list)  # directory, extraction, enrichment, manual
    ordinal: bool = False                # Hat natuerliche Ordnung?
    hierarchical: bool = False           # Hat Eltern-Kind?


class DimensionInstance(BaseModel):
    """Konkrete Instanz einer Dimension."""
    id: str = Field(default_factory=new_id)
    type_id: str                         # FK -> DimensionType.id
    name: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    parent_id: str | None = None         # Fuer hierarchische Dimensionen


class FactDimension(BaseModel):
    """Zuordnung Fakt <-> Dimension."""
    fact_id: str
    dimension_instance_id: str
    attribution_method: AttributionMethod
    confidence: float = 1.0


# ── Facts ───────────────────────────────────────────────────

class FactDefinition(BaseModel):
    """Definition eines Datenpunkt-Typs (aus YAML)."""
    id: str                              # z.B. 'effizienzwert', 'eog_jahr'
    name: str
    description: str = ""
    temporal_behavior: TemporalBehavior
    applicable_sectors: list[Sector] = Field(default_factory=list)
    value_type: ValueType = ValueType.NUMERIC
    unit: str = ""
    legal_basis: str = ""
    validation_rules: dict[str, Any] = Field(default_factory=dict)


class SourceRef(BaseModel):
    """Quellenverweis - exakte Stelle im Originaldokument."""
    document_id: str
    page: int | None = None
    paragraph: int | None = None
    text_excerpt: str = ""


class ExtractedFact(BaseModel):
    """Ein extrahierter Datenpunkt."""
    id: str = Field(default_factory=new_id)
    definition_id: str                   # FK -> FactDefinition.id
    value: str                           # Rohwert als String
    value_numeric: float | None = None   # Numerischer Wert (wenn applicable)
    unit: str = ""
    confidence: float = 0.0
    source_ref: SourceRef
    extraction_run_id: str = ""


# ── Documents ───────────────────────────────────────────────

class Document(BaseModel):
    """Ein importiertes Dokument."""
    id: str = Field(default_factory=new_id)
    file_path: str
    original_filename: str = ""
    document_type: DocumentType | None = None
    sector: Sector | None = None
    regulatory_period: str = ""
    ingestion_status: IngestionStatus = IngestionStatus.PENDING
    confidence_score: float = 0.0
    quality_flag: QualityFlag = QualityFlag.GREEN
    file_hash_sha256: str = ""
    char_count: int = 0
    page_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


# ── Legal Entities ──────────────────────────────────────────

class LegalEntity(BaseModel):
    """Ein Netzbetreiber / Marktakteur."""
    id: str = Field(default_factory=new_id)
    mastr_nr: str = ""
    bnr: str = ""
    nnr: str = ""
    name: str
    sectors: list[Sector] = Field(default_factory=list)
    state: str = ""                      # Bundesland
    city: str = ""
    zip_code: str = ""
    roles: list[str] = Field(default_factory=list)
    acer_code: str = ""
    status: str = ""                     # Aktiv/Inaktiv
    parent_entity_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


# ── Directory Definitions ───────────────────────────────────

class DirectoryDefinition(BaseModel):
    """Definition eines Datenverzeichnisses (_definition.json)."""
    id: str = Field(default_factory=new_id)
    path: str
    document_type: DocumentType
    sector: Sector
    regulatory_period: str = ""
    period_start_year: int | None = None
    period_end_year: int | None = None
    source_authority: str = ""
    source_reliability: float = 0.9
    expected_period_fixed: list[str] = Field(default_factory=list)     # FactDefinition IDs
    expected_annually_variable: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Information Spaces ──────────────────────────────────────

class DimensionFilter(BaseModel):
    """Ein Filter auf eine Dimension."""
    type_id: str
    instance_ids: list[str] | None = None   # None = alle
    instance_names: list[str] | None = None  # Alternativ: nach Name filtern


class InformationSpaceQuery(BaseModel):
    """Ein Informationsraum als Dimensions-Tupel."""
    filters: list[DimensionFilter] = Field(default_factory=list)
    fact_definition_ids: list[str] = Field(default_factory=list)


class EpistemicAssessment(BaseModel):
    """Qualitaetsbewertung eines Informationsraums."""
    completeness: float = 0.0       # 0-1
    consistency: float = 0.0        # 0-1
    reliability: float = 0.0        # 0-1
    actuality_newest: datetime | None = None
    closure: float = 0.0            # 0-1
    fact_count: int = 0
    document_count: int = 0
    entity_count: int = 0
    warnings: list[str] = Field(default_factory=list)
