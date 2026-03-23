---
name: BA/PO Agent - Produktkonzept Output
description: Output des Business Analyst / Product Owner Agents - vollstaendiges Produktkonzept mit Domaenenmodell, Features F1-F11, Datenmodellen und Phasenplanung
type: project
---

# BA/PO Agent Output - ngdai Produktkonzept

## Kontext
Der BA/PO Agent wurde mit allen Requirements aus dem Discovery-Gespraech gefuettert und hat das vollstaendige Produktkonzept erstellt.

## Kernentscheidungen

### Architektur: 3-Schichten-Modell
1. **Extraction Layer** - LLM-basierte Extraktion, Document-Level (kein Chunking)
2. **Knowledge Graph Layer** - Ontologie + Graph-DB + Vektor-Index
3. **Query Layer** - Structured Graph Query + Semantic Search + LLM-Reasoning

### Datenformat-Entscheidung
- PDF -> JSONL + TXT parallel (100% verlustfrei, validiert)
- Kein Chunking - Document-Level Extraction
- Volltext bleibt immer als Ground Truth

### 11 Features identifiziert
- F1: Legal Entity Management
- F2: Subject Matter Management
- F3: Document Ingestion Pipeline
- F4: Extraction Layer (geschlossen + offen)
- F5: Knowledge Graph + Ontologie
- F6: Query Engine (3-stufig)
- F7: Persistente Query-Templates (Snapshots + Deltas)
- F8: Analyse & Prognose (reziproke Hypothesen)
- F9: Inkonsistenz-Detektion (Regelmatrix)
- F10: Verzeichnis-Definitionen (_definition.json)
- F11: Epistemische Wissensraum-Eigenschaften

### 4 Umsetzungsphasen
1. Fundament (MVP): F10, F3, F1, F4, F5, F6
2. Breite: F3+, F4+, F2, F5+, F6+
3. Tiefe: F7, F9, F11
4. Intelligenz: F8, F6+, F3+ (Crawler), F7+

### Datenmodelle definiert
- LegalEntity mit BNR, NNR, MaStR-Nr, Sparten, Netzebenen, etc.
- SubjectMatter mit Keywords, Rechtsgrundlagen, Extraction-Prompts
- Document mit Conversion-Quality, Metadata, Extraction-Status
- Fact mit Source-Ref, Confidence, Extraction-Method
- QueryTemplate / QueryInstance / Snapshot / Delta
- EpistemicAssessment mit Completeness, Consistency, Reliability, Timeliness, Coverage
- InconsistencyResult mit Regelmatrix-Klassifikation

### Technologie-Empfehlungen
- Graph-DB: Neo4j oder Apache AGE (PostgreSQL)
- Vektor-DB: pgvector oder Qdrant
- LLM: Claude / GPT-4 via API
- Backend: Python (FastAPI)
- Task Queue: Celery + Redis oder Temporal

### Offene Designfragen (fuer Architekturphase)
1. Neo4j vs. Apache AGE?
2. Ein grosses LLM vs. spezialisierte kleinere?
3. Ontologie-Format: JSON-Schema vs. OWL/RDF?
4. UI/UX: Web-App vs. CLI vs. Notebook?
5. Single-Tenant vs. Multi-Tenant?
6. Embedding-Modell: Standard vs. Domain-specific Finetuning?
