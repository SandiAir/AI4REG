# Changelog

## [0.1.0] - 2026-03-25

Erster funktionsfaehiger MVP mit komplettem Pipeline-Durchstich.

### Features

- **F1: Legal Entity Management** - Import von MaStR-Marktakteuren (Strom + Gas) aus CSV, Fuzzy-Matching mit rapidfuzz, Parent-Child-Beziehungen (Konzern → Tochter)
- **F2: Dimensionsmodell** - 12 Dimensionstypen (legal_entity, regulatory_period, sector, region, network_level, cost_category, u.a.), YAML-basierte Konfiguration, hierarchische Dimensionen
- **F3: Ingestion Pipeline** - TXT-Dokument-Import mit automatischer Metadaten-Erkennung (Dokumenttyp, Sektor, Regulierungsperiode, Aktenzeichen), Deduplizierung per Content-Hash, Entity-Erkennung im Text
- **F4: Closed Extraction** - LLM-basierte Faktenextraktion mit Claude, Sliding Window fuer grosse Dokumente (>600K Zeichen), Doppelextraktion mit Confidence-basierter Deduplizierung, Typ-spezifische Prompts (EOG, Geschaeftsbericht)
- **F5: Knowledge Graph** - Fakten als Graph-Knoten in Apache AGE, IN_DIMENSION-Kanten zu Dimensionsinstanzen, Relationale Fallback-Queries
- **F6: Query Engine** - Regelbasiertes Query-Routing (kein LLM zur Laufzeit), Entity-Fact-Query, Vergleiche (vs), Aggregationen (Median, Durchschnitt, Min/Max)
- **F7: Web-UI** - HTMX-basiertes Dashboard mit Live-Stats, Entity-Browser mit Suche und Pagination, Dokumenten-Browser mit Typ-Filter, Query-Interface, Pico CSS Design
- **F8: Admin Panel** - Web-UI fuer Daten-Import und -Management, Seed-Funktion (Komplett-Import), Einzelaktionen (Import, Ingest, Extract), Datei-Browser
- **F9: Railway Deployment** - Auto-Deploy von GitHub (SandiAir/AI4REG), PostgreSQL + Redis als Services, Nixpacks Build, Health-Check auf /api/v1/health, PROJECT_ROOT-Erkennung fuer Railway (/app)
- **F10: Directory Definitions** - YAML-Mapping: Verzeichnispfad → Dokumenttyp → erwartete Fakten, Unterstuetzt periodenfix und jaehrlich variable Datenpunkte, Quellenzuverlaessigkeit pro Verzeichnis

### Datenstand

- 1.630 Netzbetreiber importiert (872 Strom, 758 Gas)
- 95 Dokumente ingested (40 Geschaeftsberichte, 36 EOG 3.RP, 19 EOG 4.RP)
- Faktenextraktion vorbereitet (wartet auf Anthropic API Credits)

### Datenreorganisation

Alle Dokument-Dateien in saubere `doc/` Verzeichnisstruktur verschoben:
- `doc/daten/beschluesse/3rp/` und `4rp/` (EOG-Beschluesse + Festlegungen)
- `doc/daten/geschaeftsberichte/2024/` (Geschaeftsberichte)
- `doc/daten/marktakteure/` (MaStR CSV-Exporte)
- `doc/konzept/` (Architektur- und Produktkonzept)

### Infrastruktur

- Python 3.11 + FastAPI + Uvicorn
- PostgreSQL mit Apache AGE Extension
- Redis Cache
- Railway Deployment (Procfile + railway.toml + nixpacks.toml)
- Typer CLI mit Rich-Ausgabe
- Pytest Test-Suite
