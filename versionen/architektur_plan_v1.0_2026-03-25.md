# ngdai Software-Architektur Plan

## Context

Das Produktkonzept (11 Features, 4 Phasen) ist abgeschlossen. Jetzt wird die technische Architektur entworfen, die dieses Konzept umsetzt. Greenfield-Projekt -- kein Code existiert noch.

---

## Architektur-Entscheidungen (die 9 offenen Fragen)

| # | Frage | Entscheidung | Begruendung |
|---|-------|-------------|-------------|
| 1 | Graph-DB | **Apache AGE (PostgreSQL)** | Eine DB fuer alles (relational + graph + vector). Einfacher Betrieb. Cypher-Syntax wie Neo4j. Migration moeglich. |
| 2 | LLM-Strategie | **Ein Modell, zwei Tiers**: Sonnet 4 (Extraktion), Opus 4 (Reasoning) | Regulierungsdomaene eng genug. Prompts steuern, nicht Modellwahl. |
| 3 | Ontologie-Format | **JSON-Schema** in PostgreSQL, materialisiert als AGE-Graph | Einfach, versionierbar, konsistent mit _definition.json. Kein OWL-Overhead. |
| 4 | UI/UX | **Web-UI + CLI parallel** ab Phase 1 | Web-Dashboard (HTMX + Jinja2 auf FastAPI) fuer Abfragen und Entity-Browsing. CLI fuer Admin/Batch-Operationen (ingest, extract). |
| 5 | Multi-Tenancy | **Single-Tenant** | Kein Bedarf. Saubere Modulgrenzen erlauben spaetere Erweiterung. |
| 6 | Embedding-Modell | **BGE-M3** (BAAI/bge-m3) | Deutsch-fähig, dense+sparse+ColBERT in einem, 8192 Token, lokal ausfuehrbar. |
| 7 | Thesaurus-Pflege | **Semi-automatisch**: LLM schlaegt vor, Experte bestaetigt | Bootstrap aus _definition.json + Subject-Matter-Keywords. YAML-Dateien in Git. |
| 8 | Aehnlichkeitsmetrik | **Gewichtete euklidische Distanz** | Effizienzwert wichtiger als Sektor. Gewichte konfigurierbar (YAML). Z-Score-Normalisierung. |
| 9 | Hybrid Retrieval | **Intent-gesteuert mit sequentiellem Fallback** | Router waehlt primaeren Mechanismus. Bei Leerergebnis: naechste Stufe. |

---

## System-Architektur

### Architekturmuster: Modularer Monolith

Ein Python-Prozess mit klaren internen Modulgrenzen. Spaeter zerlegbar in Services.

**Drei Runtime-Modi:**
- **Web-UI** (FastAPI + HTMX + Jinja2) -- primaere Schnittstelle fuer Abfragen, Entity-Browsing, Dokumenten-Uebersicht
- **CLI** (typer) -- Admin- und Batch-Operationen (ingest, extract, import, init)
- **Worker** -- Background-Tasks fuer Extraktion und Batch-Operationen

### Komponenten-Diagramm

```
                     +-------------------+
                     |    CLI / Web UI   |
                     +--------+----------+
                              |
                     +--------v----------+
                     |   FastAPI Server   |
                     +---+----+------+---+
                         |    |      |
            +------------+    |      +-------------+
            |                 |                     |
   +--------v-------+ +------v--------+ +---------v--------+
   | Query Engine    | | Management    | | Ingestion        |
   | (F6)            | | (F1, F2, F10) | | Pipeline (F3)    |
   +--------+-------+ +------+--------+ +---------+--------+
            |                 |                     |
   +--------v-----------------v---------------------v--------+
   |                   Core Services                          |
   |  +---------------+ +-------------+ +------------------+ |
   |  | Knowledge     | | Extraction  | | Inconsistency &  | |
   |  | Graph (F5)    | | Layer (F4)  | | Epistemic (F9,11)| |
   |  +-------+-------+ +------+------+ +--------+---------+ |
   +----------|----------------|------------------|-----------+
              |                |                  |
   +----------v----------------v------------------v-----------+
   |                   Data Layer                              |
   |  +------------+ +-----------+ +----------+ +----------+  |
   |  | PostgreSQL | | pgvector  | | File     | | Redis    |  |
   |  | + AGE      | | (in PG)  | | Storage  | | (queue)  |  |
   |  +------------+ +-----------+ +----------+ +----------+  |
   +----------------------------------------------------------+
```

---

## Generisches Dimensionsmodell

### Grundprinzip: Zwei Phasen der Dimensionierung

```
PHASE 1: Verzeichnis-Ebene (statisch, vor Extraktion)
──────────────────────────────────────────────────────
Verzeichnis dritteregulierung/EOG/
  → _definition.json liefert:
      sector=Strom, period=3.RP, doc_type=EOG
  → Diese Dimensionen sind VORAB bekannt
  → Repraesentativ fuer das Dimensionsmodell

PHASE 2: Graph-Ebene (live, nach Extraktion)
──────────────────────────────────────────────────────
Fakt ist im Knowledge Graph
  → Jetzt koennen WEITERE Dimensionen attribuiert werden:
      legal_entity  (erkannt aus Dokument)
      proceeding    (Aktenzeichen geparst)
      subject_matter (aus Extraktion abgeleitet)
      cost_category  (aus Faktentyp abgeleitet)
      region         (aus Entity-Metadaten)
      network_level  (aus Dokument-Inhalt)
      decision_chamber (aus Aktenzeichen)
      konzern        (aus Entity-Hierarchie)
      ...            (erweiterbar ohne Code-Aenderung)
```

Erst wenn Daten LIVE sind, kann das System die volle Dimensionierung vornehmen.
Die Verzeichnis-Struktur ist die **Keimzelle** — sie liefert die initialen Dimensionen,
aber der Graph fuegt weitere hinzu sobald die Fakten extrahiert und verknuepft sind.

### Meta-Modell: DimensionType + DimensionInstance

Statt hardcoded Tabellen pro Objekttyp ein generisches System:

```
dimension_types (Meta-Ebene, in YAML definiert + DB materialisiert)
    id VARCHAR PK        -- z.B. 'legal_entity', 'proceeding', 'region'
    name VARCHAR         -- Anzeigename
    description TEXT
    attributes_schema JSONB  -- welche Attribute eine Instanz haben kann
    attribution_source VARCHAR  -- 'directory' | 'extraction' | 'enrichment' | 'manual'
    ordinal BOOLEAN      -- hat natuerliche Ordnung? (year: ja, entity: nein)
    hierarchical BOOLEAN -- hat Eltern-Kind? (region: ja, period: nein)

dimension_instances (Instanz-Ebene)
    id UUID PK
    type_id VARCHAR FK -> dimension_types
    name VARCHAR NOT NULL
    attributes JSONB     -- dynamisch je nach type.attributes_schema
    parent_id UUID FK -> dimension_instances  -- fuer hierarchische Typen
    created_at TIMESTAMPTZ

fact_dimensions (N:M Zuordnung Fakt <-> Dimensionen)
    fact_id UUID FK
    dimension_instance_id UUID FK
    attribution_method VARCHAR  -- 'directory_definition' | 'extraction' | 'enrichment' | 'manual'
    confidence FLOAT
    PRIMARY KEY (fact_id, dimension_instance_id)
```

### Initiale Dimension-Types (erweiterbar per YAML)

| DimensionType | attribution_source | Beispiel-Instanzen | hierarchical |
|---|---|---|---|
| legal_entity | extraction | SW Elmshorn, Albwerk, EnBW Netz | ja (Konzern→Tochter) |
| proceeding | extraction | BK8-21-10463, BK9-22-00123 | nein |
| regulatory_period | directory | 3.RP Strom, 4.RP Gas | nein |
| calendar_year | directory+extraction | 2019, 2020, ..., 2028 | nein (aber ordinal) |
| sector | directory | Strom, Gas | nein |
| document_type | directory | EOG, KKauf, RegKonto, Geschaeftsbericht | nein |
| decision_chamber | enrichment | BK4, BK8, BK9 | nein |
| region | enrichment | NRW, Bayern, Schleswig-Holstein | ja (Bund→Land→Gebiet) |
| network_level | enrichment | HS, HS/MS, MS, MS/NS, NS | ja (Umspannung→Ebene) |
| cost_category | extraction | dnb, beeinflussbar, KKauf, VNB-Kosten | ja (Ober→Unter) |
| subject_matter | extraction+manual | Pachtkürzungen, Effizienzvergleich | nein |
| konzern | enrichment | EnBW-Gruppe, E.ON-Gruppe | ja (Holding→Tochter) |

### Dimension-Attribution-Pipeline (neue Komponente)

Nach der Extraktion laeuft automatisch die **Attribution-Pipeline** die jedem Fakt
seine Dimensionen zuweist:

```
Fakt extrahiert und im Graph
    │
    ▼
┌────────────────────────────────────────────────┐
│  Dimension Attribution Pipeline                │
│                                                │
│  1. Directory Dimensions (aus _definition.json)│
│     → sector, period, doc_type, calendar_year  │
│     → Confidence: 1.0 (definitionsbasiert)     │
│                                                │
│  2. Extraction Dimensions (aus LLM-Ergebnis)   │
│     → legal_entity (Entity-Erkennung)          │
│     → proceeding (Aktenzeichen-Parser)         │
│     → cost_category (aus Fakt-Definition)      │
│     → subject_matter (aus Fakt-Kontext)        │
│     → Confidence: 0.7-0.95 (je nach Methode)  │
│                                                │
│  3. Enrichment Dimensions (abgeleitet)         │
│     → decision_chamber (aus proceeding: BK8→)  │
│     → region (aus entity.bundesland)           │
│     → network_level (aus entity.netzebenen)    │
│     → konzern (aus entity.parent_entity)       │
│     → Confidence: 1.0 (Lookup, deterministisch)│
│                                                │
│  4. Manual Dimensions (Experte weist zu)       │
│     → subject_matter (Korrektur/Ergaenzung)    │
│     → Confidence: 1.0 (manuell)               │
└────────────────────────────────────────────────┘
```

Jeder Attributions-Schritt ist ein **Attributor** (Strategy-Pattern).
Neue DimensionTypes = neuer Attributor + YAML-Definition. Kein Core-Code-Change.

### InformationSpace als Tupel-Query

```python
class InformationSpace:
    """Beliebige Kombination von Dimensions-Filtern"""
    filters: dict[str, DimensionFilter]  # type_id -> Filter

    # Beispiele:
    space1 = InformationSpace(
        legal_entity="SW Elmshorn",
        period="4.RP Strom",
        cost_category="dnb"
    )
    space2 = InformationSpace(
        region="NRW",
        sector="Strom",
        year=range(2024, 2029)
    )

    def facts(self) -> QueryResult          # Alle Fakten in diesem Raum
    def narrow(self, **kw) -> InformationSpace   # Teilraum
    def widen(self, drop=...) -> InformationSpace # Erweiterung
    def epistemic(self) -> EpistemicAssessment    # Qualitaetsbewertung
    def compare(self, other) -> Comparison        # Raumvergleich
    def dimensions(self) -> list[DimensionType]   # Aktive Dimensionen
```

### AGE Graph-Modell (generisch)

**Knoten:**
```
(:DimensionType {id, name, hierarchical, ordinal})
(:DimensionInstance {id, type_id, name, attributes})
(:Fact {id, definition_id, value, value_numeric, unit, confidence})
(:Document {id, file_path, doc_type})
(:SourceRef {id, document_id, page, paragraph, text_excerpt})
(:FactDefinition {id, name, temporal_behavior, value_type, unit})
```

**Beziehungen:**
```
-- Kern: Fakt haengt an beliebig vielen Dimensionen
(:Fact)-[:IN_DIMENSION {method, confidence}]->(:DimensionInstance)

-- Herkunft
(:Document)-[:CONTAINS_FACT]->(:Fact)
(:Fact)-[:SOURCED_FROM]->(:SourceRef)

-- Meta
(:DimensionInstance)-[:IS_TYPE]->(:DimensionType)
(:DimensionInstance)-[:CHILD_OF]->(:DimensionInstance)  -- hierarchisch
(:DimensionInstance)-[:RELATES_TO {rel_type}]->(:DimensionInstance)  -- z.B. Entity OPERATES_IN Region

-- Fakt-Beziehungen (bleiben wie bisher)
(:Fact)-[:CONTRADICTS]->(:Fact)
(:Fact)-[:SUPERSEDES]->(:Fact)
(:Fact)-[:DEVELOPS_FROM]->(:Fact)
```

**Zentrale Aenderung:** Statt `(:Fact)-[:ABOUT_ENTITY]->(:LegalEntity)` und
`(:Fact)-[:IN_PERIOD]->(:RegulatoryPeriod)` etc. gibt es NUR NOCH die generische
`(:Fact)-[:IN_DIMENSION]->(:DimensionInstance)`. Die DimensionInstance hat einen type_id
der sagt ob es eine Entity, Period, Region etc. ist.

### Vector Storage (pgvector, in derselben PG-Instanz)

- `fact_embeddings` -- Fact-Text embedded (BGE-M3, 1024 dim)
- `source_passage_embeddings` -- Quelltext-Ausschnitte embedded
- `subject_matters.embedding` -- Subject-Matter embedded

---

## Projekt-Struktur

```
NGDAI/
├── pyproject.toml
├── alembic.ini + alembic/versions/
├── docker-compose.yml
├── config/
│   ├── settings.yaml
│   ├── thesaurus/ (synonyme.yaml, oberbegriffe.yaml, abkuerzungen.yaml)
│   ├── ontology/fact_definitions.yaml
│   └── dimensions/    (dimension_types.yaml -- alle DimensionType-Definitionen)
├── src/ngdai/
│   ├── cli/          (main.py, ingest.py, extract.py, query.py, entities.py, admin.py)
│   ├── api/          (app.py, routes/, schemas.py)
│   ├── web/          (templates/, static/)
│   │   ├── templates/ (base.html, dashboard.html, entities.html, entity_detail.html,
│   │   │               documents.html, query.html, results.html)
│   │   └── static/    (pico.min.css, htmx.min.js, app.css)
│   ├── core/         (config.py, models.py, exceptions.py, events.py, enums.py)
│   ├── db/           (engine.py, models.py, graph.py, repositories.py)
│   ├── dimensions/   (types.py, instances.py, registry.py)  -- Generisches Dimensionsmodell
│   ├── attribution/  (pipeline.py, attributors/)  -- Dimension-Attribution-Pipeline
│   │   └── attributors/ (directory.py, extraction.py, enrichment.py, manual.py)
│   ├── spaces/       (information_space.py, epistemic.py)  -- InformationSpace + Qualitaet
│   ├── definitions/  (service.py, schemas.py)       -- F10
│   ├── entities/     (service.py, detector.py, matcher.py) -- F1 (wird Attributor fuer legal_entity)
│   ├── ingestion/    (service.py, converters/, validator.py)  -- F3
│   ├── extraction/   (service.py, prompt_builder.py, sliding_window.py, validator.py) -- F4
│   ├── graph/        (service.py, ontology.py, temporal.py)  -- F5
│   ├── query/        (service.py, router.py, graph_query.py, semantic.py, response.py) -- F6
│   ├── llm/          (client.py, audit.py)
│   ├── embeddings/   (service.py)
│   └── thesaurus/    (service.py)
├── prompts/          (extraction_closed_eog.yaml, extraction_open.yaml, ...)
├── tests/
├── data/             (bestehende Daten: dritteregulierung/, vierteregulierung/, ...)
└── scripts/          (init_db.py, import_marktakteure.py, bootstrap_thesaurus.py)
```

---

## Begriffsmapping-Architektur (eigene Schicht)

Die Begriffsmapping-Schicht sitzt als **zustandslose Middleware** zwischen User-Input und Query-Engine.
Jede Anfrage wird unabhaengig verarbeitet (kein Session-Kontext in Phase 1).

```
User Input (natuerliche Sprache oder strukturiert)
    │
    ▼
┌──────────────────────────────────┐
│  Begriffsmapping Pipeline        │
│                                  │
│  1. Tokenizer/NER                │
│     → Entity-Namen erkennen      │
│     → Fachbegriffe isolieren     │
│                                  │
│  2. Intent Classifier            │
│     → strukturiert/explorativ/   │
│       vergleichend/aehnlichkeit/ │
│       analytisch                 │
│                                  │
│  3. Thesaurus Expansion          │
│     → Synonyme, Oberbegriffe,    │
│       Abkuerzungen aufloesen     │
│                                  │
│  4. Entity Resolution            │
│     → Fuzzy-Match gegen          │
│       legal_entities             │
│                                  │
│  Output: StructuredQueryIntent   │
│    {intent,                      │
│     dimensions: dict[type, filter],│
│     fact_defs[],                 │
│     free_terms[]}                │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│  Query Router                    │
│  → waehlt Mechanismus basierend  │
│    auf Intent + aufgeloesten     │
│    Termen                        │
└──┬──────┬──────┬───────┬─────────┘
   │      │      │       │
   ▼      ▼      ▼       ▼
 Graph  Embedding Feature LLM
 Query  Search   Vector  Reasoning
```

Phase 1: Nur Thesaurus-Expansion + Entity-Resolution + Graph-Query.
Phase 2: Intent-Classifier + Embedding-Search hinzu.
Phase 4: LLM-Reasoning hinzu.

## Embedding-Strategie (Nebenprodukt der Extraktion)

Embeddings entstehen **innerhalb der Extraktions-Pipeline**, nicht als separater Schritt:

```
Fakt wird extrahiert (Backoffice)
    │
    ├──→ Fakt-Text + Kontext embedden → fact_embeddings
    ├──→ source_ref.text embedden → source_passage_embeddings
    └──→ Kein extra Embedding-Pipeline-Schritt noetig
```

**Ausnahme:** Subject-Matter-Embeddings werden separat erzeugt (bei Anlage/Update eines Subject Matters).

**Vorteile gegenueber Dokument-Chunking:**
- Jedes Embedding = eine klare semantische Einheit (ein Fakt)
- Jedes Embedding rueckverfolgbar: Graph-Knoten → Source-Ref → Originaldokument
- Kein Overlap/Chunk-Boundary-Problem
- Embeddings wachsen proportional zur Wissensqualitaet

## Anti-Informationsverlust-Strategie (kein Chunking!)

ngdai verwendet an KEINER Stelle klassisches Dokument-Chunking. Zwei verschiedene Mechanismen:

### Extraktion: Sliding Window (fuer grosse Dokumente)

Wenn ein Dokument zu gross fuer das LLM-Context-Window ist:

```
Dokument (50 Seiten, 330K Zeichen)
    │
    ├─ Window 1: Seite 1-20 (+ 2 Seiten Overlap hinten)
    ├─ Window 2: Seite 19-38 (Overlap vorne + hinten)
    └─ Window 3: Seite 37-50 (Overlap vorne)

Jedes Window → eigene LLM-Extraktion → Deduplizierung
```

**Schutz gegen Informationsverlust:**
1. **Overlap**: 2 Seiten Ueberlappung an jeder Window-Grenze → Fakten die an Grenzen liegen werden in beiden Windows gefunden
2. **Deduplizierung**: Gleicher Fakt aus mehreren Windows → behalte den mit hoeherem Confidence
3. **Source-Grounding gegen Volltext**: Jeder extrahierte Fakt wird gegen den GESAMTEN Originaltext verifiziert, nicht nur gegen sein Window
4. **Vollstaendigkeits-Check**: Nach Extraktion: erwartete Felder (aus _definition.json) vs. tatsaechlich gefundene → fehlende Felder werden gemeldet
5. **Volltext bleibt**: Der TXT-Ground-Truth wird nie veraendert oder zerteilt. Nur die Extraktion arbeitet in Windows.

### Embeddings: Kein Chunking

Embeddings werden ausschliesslich auf extrahierte Fakten und Source-Passages erzeugt.
Der Volltext wird NICHT embedded und NICHT in Chunks zerteilt.
Semantische Suche laeuft ueber die Fakt-Ebene, nicht ueber Dokument-Fragmente.

---

## Pipeline-Design

### Ingestion (Backoffice): File -> DB
1. _definition.json laden (Dokumenttyp, Sektor, erwartete Felder)
2. Konvertieren zu JSONL + TXT (Phase 1: nur TXT-Passthrough)
3. Dokument in DB registrieren + Metadaten
4. Entity auto-erkennen (Aktenzeichen BK8/BK9 parsen, Fuzzy-Match)
5. Extraktions-Task dispatchen

### Extraktion (Backoffice): Dokument -> Facts -> Dimensionen
1. Extraktions-Prompt bauen (aus _definition.json + fact_definitions)
2. Doppel-Extraktion (2x LLM, Ergebnisse vergleichen)
3. Offene Extraktion (separate LLM-Anfrage, Phase 2)
4. Source Grounding pruefen (Quelltext im Original vorhanden?)
5. Regex/Range-Validierung
6. Facts in Knowledge Graph einfuegen
7. **Dimension-Attribution-Pipeline** ausfuehren:
   a. Directory-Attributor: sector, period, doc_type aus _definition.json → IN_DIMENSION Kanten
   b. Extraction-Attributor: legal_entity, proceeding, cost_category aus LLM-Ergebnis → IN_DIMENSION
   c. Enrichment-Attributor: decision_chamber, region, network_level ableiten → IN_DIMENSION
8. Post-Processing: Inkonsistenz-Check, Embeddings, temporale Verlinkung

### Query (Runtime): Frage -> InformationSpace -> Antwort
1. Begriffsmapping (Thesaurus -> Embedding -> Intent-Erkennung)
2. **InformationSpace konstruieren** aus aufgeloesten Dimensionen
   (z.B. "Pachtkürzungen NRW 4.RP" → InformationSpace(subject=Pacht, region=NRW, period=4.RP))
3. Query-Routing (strukturiert/explorativ/vergleichend/aehnlichkeit/analytisch)
4. Primaere Abfrage: Graph-Traversal ueber IN_DIMENSION Kanten
5. Fallback bei Leerergebnis (Embedding / LLM)
6. Response assemblieren + **epistemische Bewertung des InformationSpace**

---

## Phase 1 Scope (genau was gebaut wird)

### Implementierungs-Reihenfolge:

1. **Projekt-Scaffolding + DB**: pyproject.toml, Docker Compose (PG+AGE+pgvector+Redis), Alembic, Core-Module (config, models, enums), DB-Layer (engine, ORM, AGE-Helpers)

2. **F10 -- Directory Definitions**: _definition.json Schema, CLI create/list, Definitions fuer alle bestehenden Verzeichnisse, fact_definitions.yaml laden

3. **F1 -- Legal Entity Management**: CSV-Import (872 Strom + 758 Gas Marktakteure), Entity CRUD, Auto-Erkennung (Aktenzeichen-Parser), Fuzzy-Matching (rapidfuzz)

4. **F3 -- Ingestion Pipeline (TXT only)**: TXT-Converter (Passthrough + Encoding-Normalisierung), Dokument registrieren, Entity verknuepfen, alle bestehenden TXT-Dateien importieren (~95 Dateien: 51 EOG + 27 Geschaeftsberichte + Rest)

5. **F4 -- Closed Extraction (EOG + Geschaeftsberichte)**: LLM-Client (Anthropic SDK), Prompt-Templates fuer: (a) EOG-Beschluesse (Effizienzwert, Ausgangsniveau, EOG/Jahr, dnb, etc.), (b) Geschaeftsberichte (Umsatz, EBIT, Mitarbeiter, Investitionen, Netzlaenge etc.). Doppel-Extraktion, Source-Grounding, Regex-Validierung, Sliding-Window.

6. **F5 -- Knowledge Graph (Core)**: Facts als Graph-Knoten + Beziehungen einfuegen, temporale Verlinkung (DEVELOPS_FROM), Basis-Graph-Queries

7. **F6 -- Query Engine (strukturiert)**: Entity-Query, Fact-Query, Basis-Aggregation (avg, median, min/max), Basis-Vergleich (Entity A vs B)

8. **Web-UI (HTMX + Jinja2)**: Dashboard mit Entity-Uebersicht, Dokumenten-Liste, Abfrage-Interface (Suchfeld + Filter), Ergebnis-Darstellung mit Source-Refs, Entity-Detailseite. Minimales CSS (Pico CSS oder Simple.css fuer schnelles sauberes Layout).

9. **CLI**: Admin-Commands (init, import-marktakteure, definition create, ingest, extract)

### Was Phase 1 NICHT enthaelt:
- PDF/XLS/HTML-Konverter (Phase 2)
- Offene Extraktion (Phase 2)
- Subject Matter Management F2 (Phase 2)
- Embeddings + semantische Suche (Phase 2)
- Thesaurus + Intent-Klassifikation (Phase 2)
- Query-Templates F7 (Phase 3)
- Inkonsistenz-Detektion F9 (Phase 3)
- Epistemische Bewertung F11 (Phase 3)
- Analyse & Prognose F8 (Phase 4)

### Erfolgskriterien Phase 1:
1. Alle 1.630 Marktakteure als Legal Entities importiert
2. Alle ~95 TXT-Dokumente ingested (51 EOG + 27 Geschaeftsberichte + Rest)
3. Extrahierte Facts im Graph: EOG-Fakten (Effizienzwert, EOG/Jahr, Ausgangsniveau etc.) + Geschaeftsbericht-Fakten (Umsatz, EBIT, Investitionen etc.)
4. Web-UI: Dashboard mit Entity-Liste, Dokumenten-Uebersicht, Abfrage-Interface
5. Query ueber Web-UI: "Effizienzwert Stadtwerke Elmshorn" liefert korrekten Wert mit Source-Ref
6. Vergleich: "Stadtwerke Elmshorn vs. Albwerk EOG 4.RP" liefert Vergleichstabelle
7. Aggregation: "Median Effizienzwert 4.RP Strom" liefert Ergebnis
8. Kein Informationsverlust: Vollstaendigkeits-Check meldet fehlende erwartete Felder

---

## Technologie-Stack

| Komponente | Technologie |
|-----------|-------------|
| Sprache | Python 3.11+ |
| Package Manager | uv |
| Web Framework | FastAPI |
| CLI | typer |
| Web-UI | HTMX + Jinja2 (serverseitig gerendert, kein JS-Build) |
| CSS Framework | Pico CSS (classless, minimalistisch) |
| Datenbank | PostgreSQL 16 + Apache AGE + pgvector |
| ORM | SQLAlchemy 2.0 |
| Migrationen | Alembic |
| Task Queue | Redis (einfacher Worker, spaeter Celery) |
| LLM Client | anthropic SDK (Claude Sonnet 4 / Opus 4) |
| Embeddings | sentence-transformers + BGE-M3 (lokal) |
| Fuzzy Matching | rapidfuzz |
| PDF Extraktion | PyMuPDF (Phase 2) |
| Excel Parsing | openpyxl (Phase 2) |
| Testing | pytest |
| Container | Docker Compose (PG+AGE, Redis) |

---

## Risiken Phase 1

| Risiko | Mitigation |
|--------|-----------|
| AGE-Reife | Einfache Cypher-Queries reichen. Migration zu Neo4j moeglich (gleiche Sprache). |
| OCR-Artefakte in TXT | LLM kommt mit verrauschtem Text klar. Phase 2: PDF-Reprocessing. |
| Context-Window fuer grosse Dokumente | Sliding-Window von Anfang an eingebaut. Die meisten EOG-Docs passen in 200K Token. |
| LLM-Kosten (Doppel-Extraktion, ~75 Docs) | ~$135 bei Sonnet-Pricing. Akzeptabel fuer Phase 1. |

---

## Verifikation

1. `docker-compose up -d` startet PG+AGE+Redis
2. `ngdai init` erstellt DB-Schema + AGE-Graph
3. `ngdai import-marktakteure ...` importiert 1.630 Entities
4. `ngdai definition create ...` fuer EOG-Verzeichnisse
5. `ngdai ingest data/dritteregulierung/EOG/` importiert Dokumente
6. `ngdai extract --all --pending` extrahiert Facts
7. `ngdai query "Effizienzwert Stadtwerke Elmshorn"` liefert Ergebnis mit Source-Ref
8. `pytest` -- alle Tests gruen
