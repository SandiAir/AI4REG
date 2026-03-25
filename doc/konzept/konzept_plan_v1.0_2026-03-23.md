# ngdai — Produktkonzept

## 1. Produktvision

ngdai ist eine wissensbasierte Analyseplattform fuer die deutsche Netzentgeltregulierung (Strom und Gas). Sie extrahiert strukturierte Fakten aus regulatorischen Dokumenten, vernetzt diese in einem Knowledge Graph und ermoeglicht datei- und verzeichnisuebergreifende Abfragen, Trendanalysen und Hypothesenbildung mit transparenter epistemischer Bewertung.

**Kern-Wertversprechen**: Vom unstrukturierten Dokumentenstapel zur belastbaren, quantifizierbaren Regulierungsanalyse — mit nachvollziehbarer Herkunft jedes einzelnen Datenpunkts.

**Hinweis**: Die aktuellen .txt Dateien in den Verzeichnissen dienen nur als Orientierung/Referenz. Die finale Datenbasis wird aus verschiedenen Formaten (PDF, XLS, HTML, TXT) bestehen und massiv wachsen.

---

## 2. Domaenenmodell

### 2.1 Regulatorischer Kontext

```
Sparten:
  - Strom
  - Gas

Regulierungsperioden:
  Strom: 3.RP (2019-2023), 4.RP (2024-2028)
  Gas:   3.RP (2018-2022), 4.RP (2023-2027)

Dokumenttypen:
  - EOG-Beschluesse (Erlosobergrenzen-Festlegungen, BNetzA)
  - Kapitalkostenaufschlag-Beschluesse (KKauf)
  - Regulierungskonto-Beschluesse (RegKonto)
  - Geschaeftsberichte (Stadtwerke/Netzbetreiber)
  - Gerichtsurteile (OLG/BGH zu Regulierungsfragen)
  - Preisblaetter (veroeffentlichte Netzentgelte)
  - §23b-Daten (Kostenstruktur-Veroeffentlichungen)
  - §23c-Daten (Struktur-/Absatzdaten-Veroeffentlichungen)
```

### 2.2 Kern-Entities

```
Legal Entity (Netzbetreiber/Unternehmen)
  - BNR (Betreibernummer)
  - NNR (Netznummer)
  - MaStR-Nr.
  - Name, Adresse, Rechtsform
  - Sparten (Strom, Gas, ggf. beide)
  - Netzebenen (z.B. 5-7)
  - Versorgungsgebiet (Einwohner, Entnahmestellen)
  - Zustaendige Regulierungsbehoerde (BNetzA oder Landesbehoerde)
  - Verfahrensart (Regelverfahren / vereinfachtes Verfahren)

Subject Matter (Fachthema)
  - Name (z.B. "Pachtkuerzungen", "Haertefallantraege", "Effizienzvergleich")
  - Beschreibung
  - Relevante Rechtsgrundlagen (Paragraphen ARegV, EnWG)
```

### 2.3 Regulatorische Datenpunkte (Ontologie-Kern)

**Periodenfix (einmal pro RP festgelegt)**:
- Effizienzwert (%)
- Basisjahr
- EK-Zinssatz Altanlagen / Neuanlagen
- Genereller sektoraler Produktivitaetsfaktor (Xgen)
- Ausgangsniveau (EUR)
- Verfahrensart (Regel-/vereinfachtes Verfahren)

**Jaehrlich variabel (pro Kalenderjahr der RP)**:
- Kalenderjahres-Erlosobergrenze (EUR)
- Dauerhaft nicht beeinflussbare Kostenanteile (dnb-Kosten) gemaess §11 Abs. 2 ARegV (EUR) — jaehrlich neu berechnet
- Beeinflussbarer Kostenanteil (EUR)
- Voruebergehend nicht beeinflussbarer Kostenanteil (EUR)
- Erweiterungsfaktor
- Regulierungskonto-Saldo
- VPI-Anpassung
- Kapitalkostenaufschlag (KKAb)

---

## 3. Architektur — 3-Schichten-Modell

### Schicht 1: Extraction Layer
- **Geschlossene Extraktion** (ontologie-gesteuert): Bekannte Datenpunkte per Schema
- **Offene Extraktion** (explorativ): LLM-frei, Key-Value, fuer Unbekanntes
- **Feedback-Loop**: Haeufige offene Funde → werden in Ontologie aufgenommen
- **Document-Level**: Kein Chunking. Volltext bleibt Ground Truth.
- Jeder Fakt mit source_ref (Dokument, Seite, Absatz, Textstelle)

### Schicht 2: Knowledge Graph + Ontologie
- **Ontologie** = Schema (Typen, Relationen)
- **Knowledge Graph** = Instanzen (konkrete Fakten, Kanten)
- **Vektor-Index** = Sekundaer, nur Fallback fuer Semantic Search

Kern-Relationen:
```
LegalEntity --[HAS_DOCUMENT]--> Document
Document --[CONTAINS_FACT]--> Fact
Fact --[ABOUT_ENTITY]--> LegalEntity
Fact --[ABOUT_SUBJECT]--> SubjectMatter
Fact --[IN_PERIOD]--> RegulatoryPeriod
Fact --[IN_YEAR]--> CalendarYear
Fact --[SOURCED_FROM]--> SourceRef
Fact --[CONTRADICTS]--> Fact       // Inkonsistenz
Fact --[SUPERSEDES]--> Fact        // Neuere Quelle
Fact --[DEVELOPS_FROM]--> Fact     // Zeitliche Entwicklung
```

### Schicht 3: Query Layer (Hybrid, 3-stufig)
1. **Structured Graph Query** (primaer, exakt, aggregierbar)
2. **Semantic Search** (Fallback wenn Graph nicht reicht)
3. **LLM-Reasoning** (Synthese, Hypothesen, Prognosen)

---

## 4. Taxonomien

### Zeittaxonomie
```
Kalenderjahr ↔ Regulierungsperiode
  Strom: 3.RP (2019-2023), 4.RP (2024-2028)
  Gas:   3.RP (2018-2022), 4.RP (2023-2027)
```

### Definitions-Taxonomie
```
FactDefinition {
  id: string
  name: string
  temporal_behavior: PERIOD_FIXED | ANNUALLY_VARIABLE
  applicable_sectors: [Strom, Gas]
  legal_basis: string?
}
```
Bestimmt Inkonsistenz-Logik: Periodenfix-Merkmal darf sich innerhalb RP nicht aendern.

---

## 5. Features

### F1: Legal Entity Management
- User legt Unternehmen an
- Auto-Erkennung aus Dokumenten (Vorschlag mit Bestaetigung)
- Duplikat-Erkennung, Entity-Merging
- Konzernstruktur-Abbildung

### F2: Subject Matter Management
- User legt Fachthemen an
- Automatische Relevanz-Bewertung pro Dokument
- Cross-Entity-Analyse pro Thema

### F3: Document Ingestion Pipeline
- PDF → JSONL + TXT **parallel** (100% verlustfrei, validiert)
- XLS → JSONL
- HTML → JSONL + TXT
- Crawler fuer externe Quellen (v2)
- Validierung: Zeichenanzahl, Hash, Confidence-Score, Quality-Flag
- Unter Schwellwert = manuelles Review

### F4: Extraction Layer
- Geschlossene + offene Extraktion parallel
- Extraktionsschema pro Dokumenttyp (gesteuert durch F10)
- Source-Ref fuer jeden extrahierten Fakt
- Feedback-Loop: offene Funde → Ontologie-Kandidaten
- Bei Docs > Context-Window: Sliding Window mit Ueberlappung + Deduplizierung

### F5: Knowledge Graph + Ontologie
- Ontologie als erweiterbares Schema
- Graph mit allen Fakten, Relationen, Source-Refs
- Zeittaxonomie + Definitions-Taxonomie integriert
- Vektor-Index als sekundaerer Fallback

### F6: Query Engine
- User-Abfragen gegen Knowledge Graph
- Entity-Bezug, Subject-Bezug, oder Mix
- Query-Typen: Entity, Subject, Cross, Aggregation, Comparison, Trend
- Structured Query primaer, Semantic Search + LLM-Reasoning sekundaer

### F7: Persistente Query-Templates
- User definiert abstrahierte Abfrage-Graphen
- Instanziierung auf N Entities × Y Subjects × Mixes
- Snapshots + Delta-Berechnung bei neuen Daten
- Automatische Aktualisierung bei Dokument-Import
- Cross-Entity-Trend-Erkennung aus gleichen Deltas

### F8: Analyse & Prognose
- Trend-Erkennung ueber Deltas, Entities, Subject Matters
- Hypothesen werden **reziprok** abgebildet (H + NOT_H parallel geprueft)
- Hypothese → These nur wenn Guetekriterien erfuellt:
  - **Reliabilitaet** (reproduzierbar ueber verschiedene Entities)
  - **Validitaet** (misst was es messen soll)
  - **Objektivitaet** (zahlenbasiert, keine Interpretationsspielraeume)
- Guetekriterien kommen aus epistemischen Eigenschaften (F11)

### F9: Inkonsistenz-Detektion

Regelmatrix:

| Entity | Merkmal-Typ | Zeitraum | Auspraegung | Klassifikation |
|--------|-------------|----------|-------------|----------------|
| gleich | periodenfix | gleiche RP | unterschiedlich | **INKONSISTENZ** |
| gleich | periodenfix | andere RP | unterschiedlich | **PERIODENUEBERGANG** |
| gleich | variabel | gleiches Jahr | unterschiedlich | **INKONSISTENZ** |
| gleich | variabel | anderes Jahr, gleiche RP | unterschiedlich | Pruefen: **ENTWICKLUNG** oder **INKONSISTENZ** (abhaengig von Definition) |
| gleich | variabel | andere RP | unterschiedlich | **PERIODENUEBERGANG** |

Gilt fuer: Legal Entity, Subject Matter, alle Datenpunkte cross-document.

### F10: Verzeichnis-Definitionen
- Jedes Verzeichnis enthaelt `_definition.json`
- Deklariert: Dokumenttyp, Sparte, RP, Zeitraum, erwartete Datenpunkte
- Definiert periodenfix vs. variabel
- Steuert Ingestion + Extraktion
- System muss nicht raten

### F11: Epistemische Wissensraum-Eigenschaften

Jeder Informationsraum wird bewertet nach:
- **Vollstaendigkeit**: Haben wir alle Dokumente? Wissensluecken erkennen
- **Konsistenz**: Widersprueche (→ F9)
- **Verlaesslichkeit**: Quellenqualitaet (BNetzA=hoch, GB=mittel, Web=niedrig)
- **Aktualitaet**: Veraltete Daten = niedrigere Konfidenz
- **Abgeschlossenheit**: % des theoretischen Gesamtraums abgedeckt

Informationsraum-Hierarchie:
```
Gesamt-IR = Σ aller Einzel-Dokument-IRs
  ├── Entity-IR (Schnitt nach Legal Entity)
  ├── Subject-IR (Schnitt nach Thema)
  └── Mix-IR (Entity × Subject)
```

Epistemische Bewertung auf JEDER Ebene. Jede Systemantwort mit Konfidenz + Begruendung.

---

## 6. Informationsfluss (End-to-End)

```
[Quelldokument]
       |
       v
[F10: _definition.json]  → bestimmt Dokumenttyp, Sparte, RP, Datenpunkte
       |
       v
[F3: Ingestion Pipeline]  → PDF/XLS/HTML → JSONL + TXT (validiert)
       |
       v
[F1: Entity-Erkennung]  → verknuepft mit Legal Entity
       |
       v
[F4: Extraction Layer]  → geschlossene + offene Extraktion
       |
       v
[F5: Knowledge Graph]  → Fakten + Relationen + Source-Refs
       |
       ├──→ [F9: Inkonsistenz-Detektion]
       ├──→ [F7: Query-Template-Aktualisierung]
       |
       v
[F6: Query Engine]  ← User-Abfragen
       |
       v
[F8: Analyse & Prognose]  → Hypothesen + Trends
       |
       v
[F11: Epistemische Bewertung]  → Konfidenz + Begruendung
```

---

## 7. Phasen

### Phase 1: Fundament (MVP)
- F10: Verzeichnis-Definitionen
- F3: Ingestion Pipeline (TXT-Passthrough + PDF→JSONL+TXT)
- F1: Legal Entity Management
- F4: Geschlossene Extraktion (EOG-Beschluesse)
- F5: Knowledge Graph (Kern-Ontologie)
- F6: Query Engine (Structured Query, Basis-Aggregation)

### Phase 2: Breite
- F3+: XLS-Support, PDF-Verbesserung
- F4+: Extraktion fuer Geschaeftsberichte + offene Extraktion
- F2: Subject Matter Management
- F5+: Ontologie-Erweiterung
- F6+: Semantic Search Fallback

### Phase 3: Tiefe
- F7: Persistente Query-Templates + Snapshots + Deltas
- F9: Inkonsistenz-Detektion (vollstaendig)
- F11: Epistemische Bewertung (vollstaendig)

### Phase 4: Intelligenz
- F8: Analyse & Prognose mit Hypothesen-Lifecycle
- F6+: LLM-Reasoning
- F3+: Crawler
- F7+: Cross-Entity-Trend-Erkennung

---

## 8. Technologie-Empfehlungen

| Komponente | Empfehlung | Begruendung |
|-----------|------------|-------------|
| Knowledge Graph | Neo4j oder Apache AGE (PostgreSQL) | Graph-native Abfragen |
| Vektor-DB | pgvector oder Qdrant | Semantic Search Fallback |
| LLM | Claude/GPT-4 via API | Extraktion + Reasoning |
| Backend | Python (FastAPI) | ML/LLM-Oekosystem |
| Datenformat | JSONL + TXT parallel | Verlustfrei + maschinenlesbar |
| Task Queue | Celery + Redis oder Temporal | Langlebige Extraktions-Jobs |

---

## 9. Offene Designfragen (fuer Architekturphase)

1. Graph-DB: Neo4j (dediziert) vs. Apache AGE (PostgreSQL-nativ)?
2. LLM-Strategie: Ein grosses Modell vs. spezialisierte kleinere pro Extraktionstyp?
3. Ontologie-Format: JSON-Schema vs. OWL/RDF vs. PropertyGraph-Schema?
4. UI/UX: Web-App vs. CLI-first vs. Notebook-first?
5. Multi-Tenancy: Single-Tenant vs. SaaS?
6. Embedding-Modell: Domain-specific Finetuning fuer deutschen Regulierungskontext?

---

## 10. Risiken

| Risiko | Mitigation |
|--------|-----------|
| OCR-Qualitaet unzureichend | Quality-Flags, Review-Queue |
| LLM-Halluzination bei Zahlen | Doppel-Extraktion, Regex-Validierung |
| Ontologie zu starr | Offene Extraktion + Feedback-Loop |
| Context-Window zu klein fuer grosse Docs | Sliding Window + Deduplizierung |
| Skalierung auf Tausende Docs | Async Pipeline, Batch-Processing |
