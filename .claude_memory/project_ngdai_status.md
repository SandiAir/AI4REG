---
name: ngdai project status and context
description: Current state of the ngdai project - regulatory analysis platform for German grid regulation (Strom + Gas). Where we left off and what comes next.
type: project
---

## Projekt: ngdai (AI4REGU)

**Was:** Wissensbasierte Analyseplattform fuer deutsche Netzentgeltregulierung (Strom + Gas)
**GitHub:** https://github.com/StefanStanleyNGD/AI4REGU
**Phase:** Konzeptphase abgeschlossen, naechster Schritt ist Software-Architektur

## Was wir besprochen haben (Maerz 2026):

### Konzept (11 Features, 4 Phasen):
- F1: Legal Entity Management
- F2: Subject Matter Management
- F3: Document Ingestion Pipeline (PDF/XLS/HTML/TXT -> JSONL+TXT parallel, 100% verlustfrei)
- F4: Extraction Layer (geschlossene + offene Extraktion, kein Chunking)
- F5: Knowledge Graph + Ontologie
- F6: Query Engine (3-stufig: Graph Query, Semantic Search, LLM-Reasoning)
- F7: Persistente Query-Templates (Snapshots + Deltas)
- F8: Analyse & Prognose (reziproke Hypothesen, Guetekriterien)
- F9: Inkonsistenz-Detektion (Regelmatrix mit Zeittaxonomie)
- F10: Verzeichnis-Definitionen (_definition.json)
- F11: Epistemische Wissensraum-Eigenschaften

### Wichtige Korrekturen:
- dnb-Kosten sind JAEHRLICH VARIABEL (nicht periodenfix!)
- BK8 = Strom, BK9 = Gas
- Standardabfragen im Backoffice, nicht Runtime

### Datenbestand:
- 872 Strom-Netzbetreiber + 758 Gas-Netzbetreiber aus MaStR (Default Legal Entities)
- 3.RP + 4.RP Festlegungen mit Datendefinitionen und Erhebungsboegen
- Delta-Analyse 3.RP->4.RP mit Vergleichbarkeitsmatrix

### Dokumentation:
- ngdai_produktkonzept.html (ausfuehrliches Konzept fuer Menschen)
- Plan-File (technische Zusammenfassung)

## Naechster Schritt:
Software-Architekten Agent starten fuer technisches System-Design

**Why:** User will erst Konzept komplett in GitHub haben, dann beim naechsten Mal mit Architektur weitermachen.
**How to apply:** Beim naechsten Gespraech: Konzept aus GitHub lesen, Architekt-Agent starten.
