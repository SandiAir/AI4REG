---
name: Explore Agent - 4.RP Festlegung Analyse
description: Detailanalyse aller Festlegungsdokumente der 4. Regulierungsperiode Strom - inkl. Delta-Analyse zu 3.RP
type: project
---

# Explore Agent Output - 4.RP Festlegung Analyse

## Analysierte Dateien
- BK8-21-0009A Festlegung download (PDF, 34 Seiten, datiert 11.02.2022)
- BK8-21-0009-A FL_Daten_EVS4_Anlage V1 (PDF, Definitionskatalog, Stand 07.02.2022)
- BK8-21-0009-A FL_Daten_EVS4_Anlage V2_EHB (XLSX, Erhebungsbogen)
- BK 8-Festlegung Beschluss Kostendaten Strom 4.RP 25.02.2022 (PDF)
- EHB_BlSch_Kostendaten_VNB (XLSX, mit Blattschutz)
- EHB_ohneBlSch_Kostendaten_VNB (XLSX, ohne Blattschutz)
- Anlage_Bericht_Download (PDF)
- Anlage_Stellungnahmen_Download (PDF)

## 4.RP Festlegung definiert 70+ Parameter in 4 Kategorien

### A) Unternehmensdaten
- Parameter 1-10: Firmenidentifikation, Konzessionsgebiet

### B) Lastdaten
- Jahresarbeit je Netzebene (MWh)
- Jahreshoechstlast inkl. Top-5-Werte zur Validierung
- Zeitgleiche Maximallasten
- Lastprofile nach Verbrauchskategorie

### C) Absatzdaten (Parameter 16-28)
- Haushaltskunden (<10.000 kWh)
- Industriekunden (>10.000 kWh ohne RLM)
- RLM-Messlokationen (>10.000 kWh mit Registrierender Leistungsmessung)
- Strassenbeleuchtung
- Steuerbare Ladepunkte
- Nicht-steuerbare Ladepunkte (NEU in 4.RP)
- Leerstand-Messlokationen (erweiterte Definition)
- Pauschalanlagen

### D) Strukturdaten (Parameter 29-84)
- Transformatoren (nicht-regelbar, unter-Last-regelbar, Reserve)
- Schaltstationen und Kabelverteilerschraenke (WIEDERINGEFUEHRT)
- Leitungen (Erdkabel, Freileitungen, Kombinationsanlagen)
- Erzeugungsanlagen (EEG: Solar, Wind, Geothermie/Biomasse, Wasser; KWKG; Sonstige)
- Einspeisemanagement-Daten (NEU: detailliert nach Energietraeger + Netzebene)
- Installierte Erzeugungskapazitaet (NEU: mit Einspeisemanagement-Korrektur)
- Max. gleichzeitig abgeregelte Leistung (NEU)

## Kostendaten-Erhebungsbogen (4.RP) - 26 Blaetter

### Sektion A: Jahresabschluss
- A1.a: GuV 2017-2021
- A1.b: Anpassungen/Ueberleitungen
- A2.a: Bilanz 2020-2021
- A2.b: Bilanzanpassungen
- A3: Rueckstellungsspiegel 2017-2021
- A4: Darlehensspiegel 2021

### Sektion B: Kostenrechnung
- B.a: GuV Sonstiges
- B.b: Dienstleistungskosten
- B1: Kalkulatorisches EK + Gewerbesteuer
- B2.a: Netzteile
- B2.b: Kalkulatorisches Sachanlagevermoegen (Stand 31.12.2021)
- B2.c: Nutzungsdauerhistorie
- B2.d: Sonstige Anlagevermoegen
- B2.e: Anlagenspiegel
- B2.f: Anlagenabgaenge vor Ende Nutzungsdauer
- B3: Auflocsung BKZ/NKBZ

### Sektion C: Nicht beeinflussbare Kosten (dnbK)
- Gemaess §11 Abs. 2 ARegV

### Sektion D: Ergaenzende Daten (ERWEITERT in 4.RP)
- Messstellenbetrieb (MsbG)
- Blindleistung
- Regionaler Lohnniveauindex
- Staedtische Netzbetreiber-Spezifika
- Redispatch 2.0 Kosten (NEU)
- Moderne Messsysteme Kosten (NEU detaillierter)

### Sektion E: Kapitalflussrechnung (2021, optional)

### Sektion F: Kontenmapping
- F.a: Zuordnung Kontensalden zu GuV-Positionen
- F.b: Zusammenfassender Vergleich

### Sektion G: Erlaeuterungen (Freitext)

### Listen-Blatt: Dropdown-Listen fuer alle Kategorisierungen

## DELTA-ANALYSE: Was hat sich von 3.RP zu 4.RP geaendert?

### NEUE Parameter (nur 4.RP)
1. **Schaltstationen** - Wiederingefuehrt wegen hoher Erklaerungskraft im Benchmarking
2. **Nicht-steuerbare Ladepunkte** - Neue Kategorie fuer E-Mobilitaet
3. **Einspeisemanagement-Korrekturen** - Max. gleichzeitig abgeregelte Leistung, differenziert nach Energietraeger (Solar, Wind) und Netzebene
4. **Redispatch 2.0 Kosten** - Neues regulatorisches Erfordernis ab 10/2021
5. **Moderne Messsysteme (MsbG)** - Detailliertere Smart-Meter-Rollout-Kosten

### ENTFERNTE Parameter
1. **Fremdnutzungsanteile Transformatoren** - Entfernt, fuehrte zu Fehlschlussen im Benchmarking
   -> KONSEQUENZ: Transformatoren-Zahlen 3.RP vs. 4.RP NICHT VERGLEICHBAR

### GEAENDERTE Parameter
1. **Geographische Flaeche** - Definition von "Konzessionsgebiet" zu "Netzausdehnung" geaendert
   -> KONSEQUENZ: Flaechenwerte 3.RP vs. 4.RP NICHT VERGLEICHBAR
2. **Anschlusspunkte** - Detailliertere Prinzipskizzen, Klarstellung mitversorgte Gebaeude
   -> EINGESCHRAENKT VERGLEICHBAR
3. **Messlokationen Leerstand** - Erweitert auf "sehr niedrigen Verbrauch" (nicht nur Null)
   -> EINGESCHRAENKT VERGLEICHBAR
4. **Zeitgleiche Jahreshoechstlast** - Jetzt Top-5-Werte fuer Validierung
   -> VERGLEICHBAR (Hauptwert gleich)
5. **Bevoelkerungszahl** - Nebenwohnsitze weiterhin eingeschlossen, aber Dokumentation erforderlich
   -> VERGLEICHBAR

### Erhebungsbogen-Aenderungen
1. Zwei Versionen: mit/ohne Blattschutz (NEU, erleichtert Vorbereitung)
2. Neue Kostenkategorien in Sektion D
3. Erweitertes Kontenmapping (Sektion F)
4. Abgabefristen verlaengert: VNB bis 01.07.2022 (statt 30.04.), UENB bis 01.06.2022

## Vergleichbarkeitsmatrix (fuer ngdai F9 Inkonsistenz-Detektion)

### VERGLEICHBAR zwischen 3.RP und 4.RP:
- Effizienzwert
- Erlosobergrenze (EOG)
- EK-Zinssaetze
- Xgen
- Ausgangsniveau
- Jahresarbeit
- Jahreshoechstlast (Hauptwert)
- Anschlusspunkte (mit Einschraenkungen)
- Dezentrale Erzeugungsanlagen (Grundstruktur)

### NICHT VERGLEICHBAR:
- Transformatoren-Anzahl (wg. Fremdnutzungsanteile-Aenderung)
- Geographische Flaeche (wg. Definitionsaenderung)
- Schaltstationen (in 3.RP nicht erhoben)
- Ladepunkte (in 3.RP nicht differenziert)
- Einspeisemanagement-Detailwerte (in 3.RP nicht nach Energietraeger)

### EINGESCHRAENKT VERGLEICHBAR:
- Messlokationen Leerstand (erweiterte Definition)
- Anschlusspunkte (praezisere Erfassung)

## Rechtliche Referenzen (4.RP)
- Hauptfestlegung: BK8-21-0009-A (11.02.2022)
- Kostendaten: BK 8-Festlegung 25.02.2022
- Regelwerk: ARegV, StromNEV, EnWG, EEG, KWKG, MsbG
