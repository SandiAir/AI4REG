"""SQLAlchemy ORM-Modelle fuer die relationale Schicht."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ── Dimensions ──────────────────────────────────────────────

class DimensionTypeModel(Base):
    __tablename__ = "dimension_types"

    id = Column(String, primary_key=True)                  # z.B. 'legal_entity'
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    attributes_schema = Column(JSONB, default={})
    attribution_sources = Column(ARRAY(String), default=[])
    ordinal = Column(Boolean, default=False)
    hierarchical = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    instances = relationship("DimensionInstanceModel", back_populates="dimension_type")


class DimensionInstanceModel(Base):
    __tablename__ = "dimension_instances"

    id = Column(String, primary_key=True)
    type_id = Column(String, ForeignKey("dimension_types.id"), nullable=False)
    name = Column(String, nullable=False)
    attributes = Column(JSONB, default={})
    parent_id = Column(String, ForeignKey("dimension_instances.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    dimension_type = relationship("DimensionTypeModel", back_populates="instances")
    parent = relationship("DimensionInstanceModel", remote_side=[id])


# ── Fact Definitions ────────────────────────────────────────

class FactDefinitionModel(Base):
    __tablename__ = "fact_definitions"

    id = Column(String, primary_key=True)                  # z.B. 'effizienzwert'
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    temporal_behavior = Column(String, nullable=False)      # period_fixed | annually_variable
    applicable_sectors = Column(ARRAY(String), default=[])
    value_type = Column(String, default="numeric")
    unit = Column(String, default="")
    legal_basis = Column(String, default="")
    validation_rules = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.now)


# ── Directory Definitions ───────────────────────────────────

class DirectoryDefinitionModel(Base):
    __tablename__ = "directory_definitions"

    id = Column(String, primary_key=True)
    path = Column(String, nullable=False, unique=True)
    document_type = Column(String, nullable=False)
    sector = Column(String, nullable=False)
    regulatory_period = Column(String, default="")
    period_start_year = Column(Integer, nullable=True)
    period_end_year = Column(Integer, nullable=True)
    source_authority = Column(String, default="")
    source_reliability = Column(Float, default=0.9)
    expected_period_fixed = Column(JSONB, default=[])
    expected_annually_variable = Column(JSONB, default=[])
    extra_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime, default=datetime.now)


# ── Legal Entities ──────────────────────────────────────────

class LegalEntityModel(Base):
    __tablename__ = "legal_entities"

    id = Column(String, primary_key=True)
    mastr_nr = Column(String, unique=True, nullable=True)
    bnr = Column(String, nullable=True)
    nnr = Column(String, nullable=True)
    name = Column(String, nullable=False)
    sectors = Column(ARRAY(String), default=[])
    state = Column(String, default="")
    city = Column(String, default="")
    zip_code = Column(String, default="")
    roles = Column(ARRAY(String), default=[])
    acer_code = Column(String, default="")
    status = Column(String, default="")
    parent_entity_id = Column(String, ForeignKey("legal_entities.id"), nullable=True)
    extra_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    parent = relationship("LegalEntityModel", remote_side=[id])
    documents = relationship("DocumentEntityModel", back_populates="entity")


# ── Documents ───────────────────────────────────────────────

class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    file_path = Column(String, nullable=False)
    original_filename = Column(String, default="")
    document_type = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    regulatory_period = Column(String, default="")
    ingestion_status = Column(String, default="pending")
    confidence_score = Column(Float, default=0.0)
    quality_flag = Column(String, default="green")
    file_hash_sha256 = Column(String, default="")
    char_count = Column(Integer, default=0)
    page_count = Column(Integer, default=0)
    definition_id = Column(String, ForeignKey("directory_definitions.id"), nullable=True)
    extra_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime, default=datetime.now)

    entities = relationship("DocumentEntityModel", back_populates="document")


class DocumentEntityModel(Base):
    __tablename__ = "document_entities"

    document_id = Column(String, ForeignKey("documents.id"), primary_key=True)
    entity_id = Column(String, ForeignKey("legal_entities.id"), primary_key=True)
    association_type = Column(String, default="subject")   # subject, mentioned, auto_detected
    confidence = Column(Float, default=1.0)

    document = relationship("DocumentModel", back_populates="entities")
    entity = relationship("LegalEntityModel", back_populates="documents")


# ── Extraction ──────────────────────────────────────────────

class ExtractionRunModel(Base):
    __tablename__ = "extraction_runs"

    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    extraction_type = Column(String, nullable=False)       # closed, open
    model_id = Column(String, default="")
    prompt_version = Column(String, default="")
    status = Column(String, default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    extra_data = Column("metadata", JSONB, default={})


# ── Facts ───────────────────────────────────────────────────

class FactModel(Base):
    __tablename__ = "facts"

    id = Column(String, primary_key=True)
    definition_id = Column(String, ForeignKey("fact_definitions.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    extraction_run_id = Column(String, ForeignKey("extraction_runs.id"), nullable=True)
    value = Column(Text, nullable=False)
    value_numeric = Column(Float, nullable=True)
    unit = Column(String, default="")
    confidence = Column(Float, default=0.0)
    source_page = Column(Integer, nullable=True)
    source_paragraph = Column(Integer, nullable=True)
    source_text = Column(Text, default="")
    extra_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime, default=datetime.now)

    dimensions = relationship("FactDimensionModel", back_populates="fact")


class FactDimensionModel(Base):
    __tablename__ = "fact_dimensions"

    fact_id = Column(String, ForeignKey("facts.id"), primary_key=True)
    dimension_instance_id = Column(String, ForeignKey("dimension_instances.id"), primary_key=True)
    attribution_method = Column(String, nullable=False)
    confidence = Column(Float, default=1.0)

    fact = relationship("FactModel", back_populates="dimensions")
    dimension_instance = relationship("DimensionInstanceModel")


# ── Thesaurus ───────────────────────────────────────────────

class ThesaurusEntryModel(Base):
    __tablename__ = "thesaurus_entries"

    id = Column(String, primary_key=True)
    canonical_term = Column(String, nullable=False)
    entry_type = Column(String, nullable=False)            # synonym, hypernym, abbreviation, legal_ref
    variants = Column(ARRAY(String), default=[])
    target_ontology_refs = Column(ARRAY(String), default=[])
    status = Column(String, default="approved")            # approved, pending_review, rejected
    extra_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime, default=datetime.now)
