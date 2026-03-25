# ngdai - AI4REGU

Wissensbasierte Analyseplattform fuer die deutsche Netzentgeltregulierung.

**Live:** https://ngdai-app-production.up.railway.app

## Was ist ngdai?

ngdai extrahiert strukturierte Datenpunkte aus regulatorischen Dokumenten der Bundesnetzagentur (BNetzA) und Geschaeftsberichten von Netzbetreibern. Die Plattform ermoeglicht schnelle, datengetriebene Abfragen ueber Effizienzwerte, Erlosobergrenzen, Kosten und weitere regulierungsrelevante Kennzahlen - ohne manuelle Recherche.

### Kernidee

1. **Dokumente importieren** - EOG-Beschluesse, Geschaeftsberichte, Festlegungen
2. **Fakten extrahieren** - LLM-basierte Closed Extraction (einmalig, nicht zur Laufzeit)
3. **Sofort abfragen** - Strukturierte Abfragen auf vorberechneten Fakten

## Features

| Feature | Status | Beschreibung |
|---------|--------|-------------|
| F1: Legal Entity Management | Fertig | Import von MaStR-Marktakteuren, Fuzzy-Matching |
| F2: Dimensionsmodell | Fertig | 12+ Dimensionstypen (Entity, RP, Sektor, Region...) |
| F3: Ingestion Pipeline | Fertig | TXT-Import mit automatischer Metadaten-Erkennung |
| F4: Closed Extraction | Fertig | LLM-Extraktion mit Sliding Window und Doppelextraktion |
| F5: Knowledge Graph | Fertig | Fakten als Graph-Knoten (Apache AGE) |
| F6: Query Engine | Fertig | Regelbasiertes Query-Routing (Entity, Vergleich, Aggregation) |
| F7: Web-UI | Fertig | HTMX Dashboard, Entity-Browser, Dokumenten-Ansicht, Query |
| F8: Admin Panel | Fertig | Import, Ingestion, Extraktion per Web-UI |
| F9: Railway Deployment | Fertig | Auto-Deploy von GitHub, PostgreSQL + Redis |
| F10: Directory Definitions | Fertig | YAML-basierte Zuordnung Verzeichnis → Dokumenttyp → Fakten |

## Architektur

```
┌─────────────────────────────────────────────────────────┐
│                    Web-UI (HTMX + Pico CSS)             │
│  Dashboard │ Entities │ Documents │ Query │ Admin       │
├─────────────────────────────────────────────────────────┤
│                    FastAPI REST API                      │
│  /api/v1/health │ /entities │ /documents │ /query       │
│  /api/v1/admin/seed │ /import │ /ingest │ /extract      │
├─────────────────────────────────────────────────────────┤
│  Entities    │  Ingestion  │  Extraction  │  Query      │
│  Service     │  Pipeline   │  (Claude)    │  Engine     │
├─────────────────────────────────────────────────────────┤
│  Dimensions  │  Definitions │  Graph      │  LLM Client │
│  Registry    │  Service     │  Service    │  (Anthropic) │
├─────────────────────────────────────────────────────────┤
│            PostgreSQL              │      Redis          │
│  Tables + Apache AGE Graph         │    Cache            │
└─────────────────────────────────────────────────────────┘
```

## Projektstruktur

```
ngdai/
├── src/ngdai/              # Anwendungscode
│   ├── api/                # FastAPI Application + Endpoints
│   ├── cli/                # Typer CLI (init, serve, import, ingest, extract, query)
│   ├── core/               # Config, Events, Exceptions, Enums
│   ├── db/                 # SQLAlchemy Engine + ORM Models
│   ├── definitions/        # Fakt- und Verzeichnisdefinitionen (YAML)
│   ├── dimensions/         # Dimensionstyp-Registry
│   ├── entities/           # Legal Entity Management + Fuzzy-Matching
│   ├── extraction/         # LLM Closed Extraction + Prompts
│   ├── graph/              # Knowledge Graph (AGE) Service
│   ├── ingestion/          # Dokument-Ingestion Pipeline
│   ├── llm/                # Anthropic Claude API Client
│   ├── query/              # Query Engine (regelbasiert)
│   └── web/                # Templates (Jinja2 + HTMX)
├── config/                 # YAML-Konfigurationen
│   ├── dimensions/         # Dimensionstyp-Definitionen
│   ├── ontology/           # Fakt-Definitionen
│   └── directories/        # Verzeichnis → Dokumenttyp Mapping
├── doc/                    # Dokumentation und Daten
│   ├── konzept/            # Architektur- und Produktkonzept
│   └── daten/              # Regulierungsdaten
│       ├── beschluesse/    # EOG-Beschluesse (3. + 4. RP)
│       ├── geschaeftsberichte/ # Geschaeftsberichte 2024
│       ├── marktakteure/   # MaStR CSV-Exporte (Strom + Gas)
│       ├── gerichtsurteile/# (Platzhalter)
│       ├── preisblaetter/  # (Platzhalter)
│       ├── par23b/         # (Platzhalter)
│       └── par23c/         # (Platzhalter)
├── tests/                  # Pytest Test-Suite
├── scripts/                # DB-Init-Scripts (AGE Extension)
├── Procfile                # Railway Deployment
├── railway.toml            # Railway Build-Config
├── nixpacks.toml           # Nixpacks Build-Config
├── docker-compose.yml      # Lokale Entwicklung (Postgres + Redis)
└── pyproject.toml          # Python-Projekt (Hatch Build)
```

## Dimensionsmodell

Das System modelliert regulatorische Daten ueber 12 Dimensionstypen:

| Dimension | Beispiel | Hierarchie |
|-----------|----------|------------|
| legal_entity | Stadtwerke Elmshorn GmbH | Konzern → Tochter |
| regulatory_period | 4.RP (2024-2028) | - |
| calendar_year | 2024 | ordinal |
| sector | strom, gas | - |
| proceeding | BK8-21-03055 | - |
| decision_chamber | BK8 (Beschlusskammer 8) | - |
| region | Schleswig-Holstein | Bundesland |
| network_level | Hochspannung, Mittelspannung | hierarchisch |
| cost_category | dauerhaft nicht beeinflussbar | hierarchisch |
| document_type | eog, geschaeftsbericht | - |
| subject_matter | Effizienzvergleich | - |
| konzern | EnBW-Gruppe | Konzern → Tochter |

## Fakten-Definitionen

Extrahierte Datenpunkte mit Validierungsregeln:

**Periodenfix (einmal pro RP):**
- Effizienzwert (60-100%, §12 ARegV)
- Ausgangsniveau (Basiskosten)
- EK-Zinssatz alt/neu
- X-Faktor (Xgen)
- Verfahrensart (vereinfacht/Regelverfahren)

**Jaehrlich variabel:**
- EOG-Jahreswerte (EUR)
- Dauerhaft nicht beeinflussbare Kosten
- Beeinflussbare Kosten
- Erweiterungsfaktor
- Regulierungskonto-Saldo
- VPI-Anpassung

**Geschaeftsberichte:**
- Umsatz, EBIT, Mitarbeiter, Investitionen, Netzlaenge

## Schnellstart

### Lokal (Entwicklung)

```bash
# 1. Repo klonen
git clone https://github.com/SandiAir/AI4REG.git
cd AI4REG

# 2. Datenbank starten
docker-compose up -d

# 3. Python-Umgebung
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
pip install -e ".[dev]"

# 4. Konfiguration
cp .env.example .env
# ANTHROPIC_API_KEY in .env eintragen

# 5. Initialisieren und starten
ngdai init
ngdai serve
```

### Daten importieren

```bash
# Marktakteure
ngdai import-marktakteure doc/daten/marktakteure/2026-03-23_OeffentlicheMarktakteure_Strom.csv --sector strom
ngdai import-marktakteure doc/daten/marktakteure/2026-03-23_OeffentlicheMarktakteur_Gas.csv --sector gas

# Dokumente ingesten
ngdai ingest doc/daten/beschluesse/4rp
ngdai ingest doc/daten/beschluesse/3rp
ngdai ingest doc/daten/geschaeftsberichte/2024

# Fakten extrahieren (benoetigt Anthropic API Credits)
ngdai extract --all
```

### Railway (Produktion)

Die App deployed automatisch bei Push auf `main`:
- PostgreSQL und Redis als Railway-Plugins
- Environment Variables: `ANTHROPIC_API_KEY`, `NGDAI_ENV=production`
- Admin Panel: https://ngdai-app-production.up.railway.app/admin

## API Endpoints

### Oeffentlich

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| GET | `/` | Dashboard |
| GET | `/entities` | Netzbetreiber-Browser |
| GET | `/documents` | Dokumenten-Browser |
| GET | `/query?q=...` | Abfrage-Interface |
| GET | `/admin` | Admin Panel |
| GET | `/api/v1/health` | Health Check |
| GET | `/api/v1/stats` | Dashboard-Statistiken (HTMX) |
| GET | `/api/v1/entities` | Entity-Liste (HTMX, paginiert) |
| GET | `/api/v1/documents` | Dokumenten-Liste (HTMX) |
| GET | `/api/v1/query?q=...` | Query-Ergebnis (HTMX) |

### Admin API

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| POST | `/api/v1/admin/seed` | Komplett-Import (Marktakteure + alle Dokumente) |
| POST | `/api/v1/admin/import-marktakteure?sector=strom` | CSV-Import nach Sektor |
| POST | `/api/v1/admin/ingest?path=doc/daten/...` | Dokumente aus Verzeichnis importieren |
| POST | `/api/v1/admin/extract` | Alle pending Dokumente extrahieren |
| POST | `/api/v1/admin/extract-test` | Test-Extraktion eines Dokuments |
| GET | `/api/v1/admin/files` | Verfuegbare Daten-Verzeichnisse auflisten |

## Query-Beispiele

```
# Entity-Abfrage
Effizienzwert Stadtwerke Elmshorn

# Vergleich
Stadtwerke Elmshorn vs Albwerk EOG 4.RP

# Aggregation
Median Effizienzwert 4.RP Strom
```

## Tech Stack

- **Backend:** Python 3.11, FastAPI, Uvicorn
- **Frontend:** Jinja2, HTMX, Pico CSS
- **Datenbank:** PostgreSQL + Apache AGE (Knowledge Graph)
- **Cache:** Redis
- **LLM:** Anthropic Claude (Sonnet fuer Extraktion, Opus fuer Reasoning)
- **Deployment:** Railway (Nixpacks), Auto-Deploy von GitHub
- **CLI:** Typer + Rich

## Aktueller Datenstand (Produktion)

| Daten | Anzahl |
|-------|--------|
| Netzbetreiber (Strom + Gas) | 1.630 |
| Dokumente (EOG + GB) | 95 |
| EOG-Beschluesse 3. RP | 36 |
| EOG-Beschluesse 4. RP | 19 |
| Geschaeftsberichte 2024 | 40 |
| Extrahierte Fakten | Ausstehend (Anthropic Credits benoetigt) |

## Lizenz

MIT
