# -*- coding: utf-8 -*-
"""Generates the ngdai product concept as a formatted PDF."""

from fpdf import FPDF
import os

class KonzeptPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        # Use built-in fonts only (they support Latin-1)

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, "ngdai - Produktkonzept", align="L")
        self.cell(0, 8, "Stand: Maerz 2026", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 102, 178)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Seite {self.page_no()}/{{nb}}", align="C")

    def chapter_title(self, title):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(0, 51, 102)
        self.ln(6)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 102, 178)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(0, 76, 140)
        self.ln(3)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def subsection_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(51, 51, 51)
        self.ln(2)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(33, 33, 33)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bold_text(self, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(33, 33, 33)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def bullet(self, text, indent=10):
        x = self.get_x()
        self.set_font("Helvetica", "", 10)
        self.set_text_color(33, 33, 33)
        self.cell(indent)
        self.cell(5, 5.5, "-")
        self.multi_cell(0, 5.5, text)

    def bullet_bold_desc(self, bold_part, desc):
        x = self.get_x()
        self.cell(10)
        self.cell(5, 5.5, "-")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(33, 33, 33)
        w_bold = self.get_string_width(bold_part + " ")
        self.cell(w_bold, 5.5, bold_part + " ")
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5.5, desc)

    def add_table(self, headers, rows, col_widths=None):
        if col_widths is None:
            n = len(headers)
            col_widths = [190 / n] * n

        # Header
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(0, 76, 140)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()

        # Rows
        self.set_font("Helvetica", "", 9)
        self.set_text_color(33, 33, 33)
        fill = False
        for row in rows:
            max_h = 7
            # Calculate row height
            for i, cell in enumerate(row):
                lines = self.multi_cell(col_widths[i], 5.5, str(cell), split_only=True)
                h = len(lines) * 5.5
                if h > max_h:
                    max_h = h

            if fill:
                self.set_fill_color(240, 245, 250)
            else:
                self.set_fill_color(255, 255, 255)

            y_start = self.get_y()
            x_start = self.get_x()

            for i, cell in enumerate(row):
                x = x_start + sum(col_widths[:i])
                self.set_xy(x, y_start)
                self.multi_cell(col_widths[i], 5.5, str(cell), border=1, fill=True)

            # Move to consistent position
            self.set_y(y_start + max_h)
            fill = not fill
        self.ln(3)

    def add_simple_table(self, headers, rows, col_widths=None):
        """Simple table with single-line cells."""
        if col_widths is None:
            n = len(headers)
            col_widths = [190 / n] * n

        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(0, 76, 140)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()

        self.set_font("Helvetica", "", 9)
        self.set_text_color(33, 33, 33)
        fill = False
        for row in rows:
            if fill:
                self.set_fill_color(240, 245, 250)
            else:
                self.set_fill_color(255, 255, 255)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 6.5, str(cell), border=1, fill=True)
            self.ln()
            fill = not fill
        self.ln(3)

    def code_block(self, text):
        self.set_font("Courier", "", 8)
        self.set_text_color(33, 33, 33)
        self.set_fill_color(245, 245, 245)
        self.set_draw_color(200, 200, 200)
        y = self.get_y()
        lines = text.split("\n")
        h = len(lines) * 4.5 + 6
        if y + h > 270:
            self.add_page()
        self.rect(10, self.get_y(), 190, h)
        self.set_xy(13, self.get_y() + 3)
        for line in lines:
            self.cell(0, 4.5, line, new_x="LMARGIN", new_y="NEXT")
            self.set_x(13)
        self.ln(5)


def sanitize(text):
    """Replace special chars that aren't in Latin-1."""
    replacements = {
        "\u2192": "->",    # →
        "\u2190": "<-",    # ←
        "\u2194": "<->",   # ↔
        "\u2013": "-",     # –
        "\u2014": "--",    # —
        "\u2018": "'",     # '
        "\u2019": "'",     # '
        "\u201c": '"',     # "
        "\u201d": '"',     # "
        "\u2022": "-",     # •
        "\u03a3": "Summe", # Σ
        "\u2265": ">=",    # ≥
        "\u2264": "<=",    # ≤
        "\u00d7": "x",     # ×
        "\u2026": "...",   # …
        "\u2713": "[OK]",  # ✓
        "\u2717": "[X]",   # ✗
        "\u0308": "",      # combining umlaut (shouldn't appear but safety)
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def build_pdf():
    pdf = KonzeptPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # =========================================================================
    # TITLE PAGE
    # =========================================================================
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 15, "ngdai", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "Produktkonzept", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, "Wissensbasierte Analyseplattform", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, sanitize("fuer die deutsche Netzentgeltregulierung"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_draw_color(0, 102, 178)
    pdf.set_line_width(0.8)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, "Sparten: Strom & Gas", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "Status: Greenfield / Konzeptphase", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "Stand: Maerz 2026", align="C", new_x="LMARGIN", new_y="NEXT")

    # =========================================================================
    # 1. PRODUKTVISION
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("1. Produktvision")
    pdf.body_text(sanitize(
        "ngdai ist eine wissensbasierte Analyseplattform fuer die deutsche Netzentgeltregulierung "
        "(Strom und Gas). Sie extrahiert strukturierte Fakten aus regulatorischen Dokumenten, "
        "vernetzt diese in einem Knowledge Graph und ermoeglicht datei- und verzeichnisuebergreifende "
        "Abfragen, Trendanalysen und Hypothesenbildung mit transparenter epistemischer Bewertung."
    ))
    pdf.bold_text(sanitize(
        "Kern-Wertversprechen: Vom unstrukturierten Dokumentenstapel zur belastbaren, "
        "quantifizierbaren Regulierungsanalyse -- mit nachvollziehbarer Herkunft jedes einzelnen Datenpunkts."
    ))
    pdf.body_text(sanitize(
        "Hinweis: Die aktuellen Textdateien in den Verzeichnissen dienen nur als Orientierung. "
        "Die finale Datenbasis wird aus verschiedenen Formaten (PDF, XLS, HTML, TXT) bestehen und massiv wachsen."
    ))

    # =========================================================================
    # 2. DOMAENENMODELL
    # =========================================================================
    pdf.chapter_title(sanitize("2. Domaenenmodell"))

    pdf.section_title("2.1 Regulatorischer Kontext")
    pdf.bold_text("Sparten:")
    pdf.bullet("Strom")
    pdf.bullet("Gas")
    pdf.ln(2)

    pdf.bold_text(sanitize("Regulierungsperioden:"))
    pdf.add_simple_table(
        ["Sparte", "3. Regulierungsperiode", "4. Regulierungsperiode"],
        [
            ["Strom", "2019 - 2023", "2024 - 2028"],
            ["Gas", "2018 - 2022", "2023 - 2027"],
        ],
        [40, 75, 75]
    )

    pdf.bold_text("Dokumenttypen:")
    pdf.add_simple_table(
        ["Dokumenttyp", "Beschreibung", "Quelle"],
        [
            ["EOG-Beschluesse", "Erlosobergrenzen-Festlegungen", "BNetzA (BK8/BK9)"],
            ["KKauf-Beschluesse", "Kapitalkostenaufschlag", "BNetzA"],
            ["RegKonto-Beschluesse", "Regulierungskonto", "BNetzA"],
            [sanitize("Geschaeftsberichte"), "Jahresberichte Stadtwerke/Netzbetreiber", "Unternehmen"],
            ["Gerichtsurteile", "OLG/BGH zu Regulierungsfragen", "Gerichte"],
            [sanitize("Preisblaetter"), sanitize("Veroeffentlichte Netzentgelte"), "Netzbetreiber"],
            [sanitize("Paragraph 23b-Daten"), sanitize("Kostenstruktur-Veroeffentlichungen"), "Netzbetreiber"],
            [sanitize("Paragraph 23c-Daten"), sanitize("Struktur-/Absatzdaten"), "Netzbetreiber"],
        ],
        [50, 85, 55]
    )

    pdf.section_title("2.2 Kern-Entities")
    pdf.bold_text("Legal Entity (Netzbetreiber/Unternehmen):")
    pdf.add_simple_table(
        ["Attribut", "Beschreibung"],
        [
            ["BNR", "Betreibernummer (BNetzA)"],
            ["NNR", "Netznummer"],
            ["MaStR-Nr.", "Marktstammdatenregister-Nummer"],
            ["Name / Adresse / Rechtsform", "Stammdaten"],
            ["Sparten", "Strom, Gas oder beides"],
            ["Netzebenen", "z.B. 5-7"],
            ["Versorgungsgebiet", "Einwohner, Entnahmestellen"],
            [sanitize("Regulierungsbehoerde"), "BNetzA oder Landesbehoerde"],
            ["Verfahrensart", "Regelverfahren / vereinfachtes Verfahren"],
        ],
        [60, 130]
    )

    pdf.bold_text("Subject Matter (Fachthema):")
    pdf.add_simple_table(
        ["Attribut", "Beschreibung"],
        [
            ["Name", sanitize("z.B. Pachtkuerzungen, Haertefallantraege")],
            ["Beschreibung", "Thematische Definition"],
            ["Rechtsgrundlagen", "Relevante Paragraphen ARegV, EnWG"],
        ],
        [60, 130]
    )

    pdf.section_title("2.3 Regulatorische Datenpunkte (Ontologie-Kern)")
    pdf.bold_text("Periodenfix (einmal pro Regulierungsperiode festgelegt):")
    pdf.add_simple_table(
        ["Datenpunkt", "Typ", "Einheit"],
        [
            ["Effizienzwert", "Numerisch", "%"],
            ["Basisjahr", "Numerisch", "Jahr"],
            ["EK-Zinssatz Altanlagen", "Numerisch", "%"],
            ["EK-Zinssatz Neuanlagen", "Numerisch", "%"],
            [sanitize("Xgen (Produktivitaetsfaktor)"), "Numerisch", "%"],
            ["Ausgangsniveau", "Numerisch", "EUR"],
            [sanitize("dnb-Kosten (Paragraph 11 Abs. 2 ARegV)"), "Numerisch", "EUR"],
            ["Verfahrensart", "Kategorial", "-"],
        ],
        [80, 50, 60]
    )

    pdf.bold_text(sanitize("Jaehrlich variabel (pro Kalenderjahr der RP):"))
    pdf.add_simple_table(
        ["Datenpunkt", "Typ", "Einheit"],
        [
            ["Erlosobergrenze (EOG)", "Numerisch", "EUR/Jahr"],
            ["Beeinflussbarer Kostenanteil", "Numerisch", "EUR"],
            [sanitize("Voruebergehend nicht beeinflussbarer Anteil"), "Numerisch", "EUR"],
            ["Erweiterungsfaktor", "Numerisch", "dimensionslos"],
            ["Regulierungskonto-Saldo", "Numerisch", "EUR"],
            ["VPI-Anpassung", "Numerisch", "%"],
            ["Kapitalkostenaufschlag (KKAb)", "Numerisch", "EUR"],
        ],
        [80, 50, 60]
    )

    # =========================================================================
    # 3. ARCHITEKTUR
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("3. Architektur -- 3-Schichten-Modell")

    pdf.add_simple_table(
        ["Schicht", "Funktion", "Methode"],
        [
            ["1. Extraction Layer", "Dokumente -> strukturierte Fakten", "LLM-basiert, Document-Level (kein Chunking)"],
            ["2. Knowledge Graph", sanitize("Vernetzung aller Fakten"), "Ontologie + Graph-DB + Vektor-Index"],
            ["3. Query Layer", "Hybride Abfragen", "Graph Query + Semantic Search + LLM-Reasoning"],
        ],
        [45, 65, 80]
    )

    pdf.section_title("3.1 Extraction Layer")
    pdf.body_text(sanitize(
        "Zwei Extraktionsmodi laufen parallel:"
    ))
    pdf.add_simple_table(
        ["Modus", "Beschreibung", "Output"],
        [
            ["Geschlossene Extraktion", "Ontologie-gesteuert, bekannte Datenpunkte per Schema", "Typisierte Fakten mit Source-Ref"],
            ["Offene Extraktion", sanitize("Explorativ, LLM findet unbekannte Datenpunkte"), "Key-Value-Paare mit Kategorie-Vorschlag"],
        ],
        [50, 80, 60]
    )
    pdf.body_text(sanitize(
        "Feedback-Loop: Haeufige offene Funde (>= N Dokumente) werden als Ontologie-Kandidaten vorgeschlagen. "
        "Nach Review durch Domaenenexperten: Aufnahme in Extraktionsschema + rueckwirkende Extraktion auf Altdokumente."
    ))
    pdf.body_text(sanitize(
        "Wichtig: Kein Chunking. Document-Level Extraction. Volltext bleibt immer als Ground Truth erhalten. "
        "Jeder extrahierte Fakt hat eine Source-Ref (Dokument, Seite, Absatz, Textstelle)."
    ))
    pdf.body_text(sanitize(
        "Bei Dokumenten groesser als Context-Window: Seitenweises Sliding Window mit Ueberlappung und Deduplizierung."
    ))

    pdf.section_title("3.2 Knowledge Graph + Ontologie")
    pdf.add_simple_table(
        ["Komponente", "Rolle", "Beispiel"],
        [
            ["Ontologie", "Schema: definiert Typen und Relationen", sanitize("'Kuerzung' ist ein Faktentyp mit Betrag + Kategorie")],
            ["Knowledge Graph", "Instanzen: konkrete Fakten und Kanten", sanitize("SW Elmshorn -> hat Kuerzung -> Pacht -> 234.000 EUR")],
            [sanitize("Vektor-Index"), sanitize("Sekundaer: Fallback fuer Semantic Search"), "Embedding-Suche wenn Graph nicht ausreicht"],
        ],
        [40, 70, 80]
    )

    pdf.bold_text("Kern-Relationen im Graph:")
    pdf.add_simple_table(
        ["Relation", "Von", "Nach"],
        [
            ["HAS_DOCUMENT", "LegalEntity", "Document"],
            ["CONTAINS_FACT", "Document", "Fact"],
            ["ABOUT_ENTITY", "Fact", "LegalEntity"],
            ["ABOUT_SUBJECT", "Fact", "SubjectMatter"],
            ["IN_PERIOD", "Fact", "RegulatoryPeriod"],
            ["IN_YEAR", "Fact", "CalendarYear"],
            ["SOURCED_FROM", "Fact", "SourceRef"],
            ["CONTRADICTS", "Fact", "Fact (Inkonsistenz)"],
            ["SUPERSEDES", "Fact", "Fact (neuere Quelle)"],
            ["DEVELOPS_FROM", "Fact", "Fact (zeitl. Entwicklung)"],
        ],
        [50, 60, 80]
    )

    pdf.section_title("3.3 Query Layer (3-stufig)")
    pdf.add_simple_table(
        ["Stufe", "Methode", "Wann", "Eigenschaft"],
        [
            [sanitize("1 (primaer)"), "Structured Graph Query", "Immer zuerst", "Exakt, aggregierbar, zaehlbar"],
            ["2 (Fallback)", "Semantic Search", "Wenn Graph nicht reicht", sanitize("Fuzzy, niedrigerer Confidence-Score")],
            ["3 (Synthese)", "LLM-Reasoning", sanitize("Fuer Hypothesen/Prognosen"), "Kombiniert Graph + Text"],
        ],
        [30, 50, 50, 60]
    )

    # =========================================================================
    # 4. TAXONOMIEN
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("4. Taxonomien")

    pdf.section_title("4.1 Zeittaxonomie")
    pdf.body_text(sanitize(
        "Die Zeitachse ist nicht linear, sondern hat eine regulatorische Struktur: "
        "Kalenderjahre sind in Regulierungsperioden eingebettet. Strom und Gas haben "
        "unterschiedliche Perioden-Zeitraeume."
    ))
    pdf.add_simple_table(
        ["Ebene", "Beschreibung", "Bedeutung"],
        [
            ["Kalenderjahr", "2022, 2023, 2024, ...", "Operative Ebene (EOG pro Jahr)"],
            ["Regulierungsperiode", "3.RP, 4.RP (je Sparte)", sanitize("Strategische Ebene (Effizienzwert, Xgen)")],
            [sanitize("Periodenwechsel"), "z.B. 2023->2024 (Strom)", sanitize("Erwartbare Aenderungen, kein Widerspruch")],
        ],
        [45, 65, 80]
    )

    pdf.section_title("4.2 Definitions-Taxonomie")
    pdf.body_text(sanitize(
        "Jeder Datenpunkt hat ein definiertes zeitliches Verhalten. "
        "Dies ist entscheidend fuer die Inkonsistenz-Detektion (F9):"
    ))
    pdf.add_simple_table(
        ["Verhalten", "Bedeutung", sanitize("Aenderung innerhalb RP"), "Beispiele"],
        [
            ["PERIOD_FIXED", "Einmal pro RP festgelegt", sanitize("= INKONSISTENZ"), "Effizienzwert, Xgen, EK-Zins"],
            ["ANNUALLY_VARIABLE", sanitize("Aendert sich jaehrlich"), sanitize("= moegl. Entwicklung"), "EOG, RegKonto, Erweiterungsfaktor"],
        ],
        [38, 48, 50, 54]
    )

    # =========================================================================
    # 5. FEATURES
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title(sanitize("5. Features -- Detailspezifikation"))

    # F1
    pdf.section_title("F1: Legal Entity Management")
    pdf.body_text("User legt Unternehmen/Netzbetreiber an und verwaltet sie.")
    pdf.add_simple_table(
        ["Funktion", "Beschreibung"],
        [
            ["CRUD", "Anlegen, Bearbeiten, Loeschen von Entities"],
            ["Auto-Erkennung", "System erkennt Entities aus Dokumenten (Vorschlag + Bestaetigung)"],
            ["Duplikat-Erkennung", "Ueber BNR, NNR, MaStR-Nr, Namens-Fuzzy-Match"],
            ["Entity-Merging", "Zusammenfuehren erkannter Duplikate"],
            ["Konzernstruktur", "Stadtwerk -> Netzgesellschaft -> Mutterkonzern"],
            ["Dokument-Zuordnung", "Manuell + automatisch via Name/BNR-Matching"],
        ],
        [50, 140]
    )

    # F2
    pdf.section_title("F2: Subject Matter Management")
    pdf.body_text("User legt Fachthemen an als orthogonale Dimension zu Legal Entities.")
    pdf.add_simple_table(
        ["Funktion", "Beschreibung"],
        [
            ["CRUD", "Anlegen, Bearbeiten, Loeschen von Subject Matters"],
            ["Relevanz-Bewertung", "Automatischer Score (0.0-1.0) pro Dokument"],
            ["Cross-Entity-Analyse", "Wie behandeln verschiedene Netzbetreiber dasselbe Thema?"],
            ["Themen-Clustering", "System schlaegt neue Subjects vor (aus offener Extraktion)"],
        ],
        [50, 140]
    )

    # F3
    pdf.section_title("F3: Document Ingestion Pipeline")
    pdf.body_text(sanitize(
        "Verlustfreie Konvertierung aller Quellformate. 100% Texterhalt, validiert."
    ))
    pdf.add_simple_table(
        ["Quellformat", "Zielformate", "Validierung"],
        [
            ["PDF", "JSONL + TXT (parallel)", "Zeichenanzahl, Hash, Visual Diff"],
            ["XLS/XLSX", "JSONL", "Schema-Validierung, Zellcount"],
            ["HTML", "JSONL + TXT", "DOM-Vergleich, Textcontent-Hash"],
            ["TXT", "JSONL (Passthrough)", "Length-Check"],
        ],
        [40, 60, 90]
    )

    pdf.bold_text(sanitize("Qualitaetsschwellen:"))
    pdf.add_simple_table(
        ["Confidence Score", "Flag", "Aktion"],
        [
            [">= 0.95", "GREEN", "Automatisch weiter"],
            [">= 0.80", "YELLOW", "Warnung, automatisch weiter, Review-Queue"],
            ["< 0.80", "RED", "Stopp, manuelles Review erforderlich"],
        ],
        [50, 40, 100]
    )

    pdf.bold_text("Crawler (v2): Automatisches Abgreifen externer Quellen (BNetzA-Website, Bundesanzeiger, etc.)")

    # F4
    pdf.section_title("F4: Extraction Layer")
    pdf.body_text(sanitize(
        "LLM-basierte Extraktion strukturierter Fakten. Geschlossene + offene Extraktion parallel. "
        "Document-Level (kein Chunking). Jeder Fakt mit Source-Ref."
    ))
    pdf.add_simple_table(
        ["Aspekt", "Detail"],
        [
            ["Extraktionsschema", "Pro Dokumenttyp (gesteuert durch _definition.json / F10)"],
            ["Source-Ref", "Dokument, Seite, Absatz, Zeilenbereich, Textsnippet"],
            ["Feedback-Loop", sanitize("Offene Funde >= N Dokumente -> Ontologie-Kandidat")],
            ["Grosse Dokumente", sanitize("Sliding Window mit Ueberlappung + Deduplizierung")],
            ["Validierung", "Regex-Patterns, Doppel-Extraktion mit Abgleich"],
        ],
        [50, 140]
    )

    # F5
    pdf.section_title("F5: Knowledge Graph + Ontologie")
    pdf.body_text(sanitize(
        "Zentrale Vernetzung aller extrahierten Fakten. Ontologie als erweiterbares Schema. "
        "Zeittaxonomie + Definitions-Taxonomie integriert."
    ))
    pdf.add_simple_table(
        ["Ontologie-Element", "Beschreibung"],
        [
            ["Kern-Klassen", "LegalEntity, Document, SubjectMatter, Fact, RegulatoryPeriod, CalendarYear"],
            [sanitize("Faktentypen"), "NumericFact, CategoricalFact, TextFact, TemporalFact"],
            ["Zeittaxonomie", sanitize("Kalenderjahr <-> Regulierungsperiode (je Sparte)")],
            ["Definitions-Taxonomie", "PERIOD_FIXED vs. ANNUALLY_VARIABLE pro Datenpunkt"],
            ["Erweiterung", "Schema-driven, ohne Code-Aenderung"],
        ],
        [50, 140]
    )

    # F6
    pdf.add_page()
    pdf.section_title("F6: Query Engine")
    pdf.body_text(sanitize(
        "Hybride Abfragen. Structured Graph Query primaer, Semantic Search + LLM-Reasoning sekundaer."
    ))
    pdf.add_simple_table(
        ["Query-Typ", "Beschreibung", "Beispiel"],
        [
            ["Entity-Query", "Alle Fakten zu einer Entity", "Alle EOG-Werte der SW Elmshorn"],
            ["Subject-Query", sanitize("Alle Fakten zu einem Thema"), sanitize("Alle Haertefallantraege ueber alle Netzbetreiber")],
            ["Cross-Query", "Entity x Subject", sanitize("Pachtkuerzungen bei Stadtwerken in NRW")],
            ["Aggregation", "Statistische Auswertung", "Median-Effizienzwert 4.RP Strom"],
            ["Comparison", "Entity vs. Entity", "EOG Elmshorn vs. Karlsruhe 2024-2028"],
            ["Trend", "Zeitliche Entwicklung", sanitize("Entwicklung dnb-Anteil 3.RP -> 4.RP")],
        ],
        [35, 60, 95]
    )

    # F7
    pdf.section_title("F7: Persistente Query-Templates")
    pdf.body_text(sanitize(
        "User definiert abstrahierte Abfrage-Graphen, die auf N Entities x Y Subjects x Mixes instanziiert werden. "
        "Bei jedem Daten-Import: automatische Neuausfuehrung, Snapshot, Delta-Berechnung."
    ))
    pdf.add_simple_table(
        ["Komponente", "Beschreibung"],
        [
            ["QueryTemplate", "Abstrakte, parametrisierbare Abfrage"],
            ["QueryInstance", "Konkrete Instanz (Template + Parameter-Bindung)"],
            ["Snapshot", "Ergebnis zu einem Zeitpunkt (nach Import)"],
            ["Delta", sanitize("Aenderungen zwischen Snapshots (ADDED, REMOVED, MODIFIED)")],
            ["Trend-Erkennung", sanitize(">= K Instanzen mit gleichem Delta-Typ -> Systemweiter Trend")],
        ],
        [45, 145]
    )

    # F8
    pdf.section_title(sanitize("F8: Analyse & Prognose"))
    pdf.body_text(sanitize(
        "Ableitung von Hypothesen aus Query-Deltas und Cross-Entity-Mustern. "
        "Hypothesen werden REZIPROK abgebildet (H + NOT_H parallel geprueft)."
    ))
    pdf.bold_text(sanitize("Hypothese wird zur These nur wenn Guetekriterien erfuellt:"))
    pdf.add_simple_table(
        [sanitize("Guetekriterium"), "Definition", "Messung"],
        [
            [sanitize("Reliabilitaet"), "Ergebnis ist reproduzierbar", "count(entities_confirming) / count(entities_total)"],
            [sanitize("Validitaet"), "Misst was es messen soll", sanitize("Query-Template-Praezision gegen Stichprobe")],
            [sanitize("Objektivitaet"), sanitize("Unabhaengig vom Betrachter"), "1.0=nur Zahlen, 0.5=Mix, 0.0=nur Text"],
        ],
        [40, 55, 95]
    )

    # F9
    pdf.section_title(sanitize("F9: Inkonsistenz-Detektion"))
    pdf.body_text(sanitize(
        "Automatischer Cross-Dokument-Abgleich aller Datenpunkte mit regelbasierter Klassifikation."
    ))
    pdf.add_simple_table(
        ["Entity", "Merkmal-Typ", "Zeitraum", sanitize("Auspraegung"), "Klassifikation"],
        [
            ["gleich", "periodenfix", "gleiche RP", "unterschiedlich", "INKONSISTENZ"],
            ["gleich", "periodenfix", "andere RP", "unterschiedlich", sanitize("PERIODENUEBERGANG")],
            ["gleich", "variabel", "gleiches Jahr", "unterschiedlich", "INKONSISTENZ"],
            ["gleich", "variabel", sanitize("anderes Jahr, gl. RP"), "unterschiedlich", sanitize("Pruefen: ENTWICKLUNG oder INKONSISTENZ")],
            ["gleich", "variabel", "andere RP", "unterschiedlich", sanitize("PERIODENUEBERGANG")],
            ["verschieden", "beliebig", "gleicher Zeitraum", "unterschiedlich", "VARIATION (Benchmark)"],
        ],
        [28, 32, 40, 38, 52]
    )
    pdf.body_text(sanitize(
        "Gilt fuer: Legal Entity, Subject Matter, alle Datenpunkte cross-document. "
        "Schweregrade: CRITICAL, WARNING, INFO. Resolution-Tracking pro Inkonsistenz."
    ))

    # F10
    pdf.section_title("F10: Verzeichnis-Definitionen")
    pdf.body_text(sanitize(
        "Jedes Datenverzeichnis enthaelt eine _definition.json die deklariert, "
        "welche Dokumenttypen es enthaelt und welche Datenpunkte erwartet werden. "
        "Das System muss nicht raten -- es weiss was drin liegt."
    ))
    pdf.add_simple_table(
        ["Feld", "Beschreibung", "Beispiel"],
        [
            ["document_type", "Typ der enthaltenen Dokumente", "EOG_Beschluss"],
            ["sector", "Sparte", "Strom"],
            ["regulatory_period", "Regulierungsperiode", "3.RP"],
            ["period_years", "Zeitraum", "2019-2023"],
            ["expected_data_points", "Erwartete Datenpunkte (fix + variabel)", "Effizienzwert, EOG, ..."],
            ["source_reliability", sanitize("Quellenverlaesslichkeit"), "1.0 (BNetzA)"],
        ],
        [45, 75, 70]
    )

    # F11
    pdf.add_page()
    pdf.section_title("F11: Epistemische Wissensraum-Eigenschaften")
    pdf.body_text(sanitize(
        "Jeder Informationsraum wird nach Wissensqualitaet bewertet. "
        "Jede Systemantwort enthaelt Konfidenz + Begruendung."
    ))
    pdf.add_simple_table(
        ["Eigenschaft", "Beschreibung", "Beispiel"],
        [
            [sanitize("Vollstaendigkeit"), sanitize("Haben wir alle relevanten Dokumente?"), "19/180 Beschluesse = 10.5%"],
            ["Konsistenz", sanitize("Widersprueche erkannt? (-> F9)"), sanitize("3 Inkonsistenzen bei Entity X")],
            [sanitize("Verlaesslichkeit"), sanitize("Quellenqualitaet"), "BNetzA=hoch, GB=mittel, Web=niedrig"],
            [sanitize("Aktualitaet"), sanitize("Wie alt sind die Daten?"), sanitize("Neustes Dok: 06/2024")],
            ["Abgeschlossenheit", "% des theoretischen Gesamtraums", sanitize("62% der Netzbetreiber abgedeckt")],
        ],
        [38, 72, 80]
    )

    pdf.bold_text(sanitize("Informationsraum-Hierarchie:"))
    pdf.add_simple_table(
        ["Ebene", "Beschreibung", "Beispiel"],
        [
            ["Gesamt-IR", "Summe aller Einzel-Dokument-IRs", "Alle 95+ Dokumente"],
            ["Entity-IR", "Schnitt nach Legal Entity", "Alles ueber SW Elmshorn"],
            ["Subject-IR", "Schnitt nach Thema", sanitize("Alle Pachtkuerzungen")],
            ["Mix-IR", "Entity x Subject", sanitize("Pachtkuerzungen bei SW Elmshorn")],
        ],
        [35, 65, 90]
    )
    pdf.body_text("Epistemische Bewertung wird auf JEDER Ebene berechnet.")

    # =========================================================================
    # 6. INFORMATIONSFLUSS
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("6. Informationsfluss (End-to-End)")
    pdf.add_simple_table(
        ["Schritt", "Komponente", "Input", "Output"],
        [
            ["1", "F10: _definition.json", "Verzeichnispfad", "Dokumenttyp, Sparte, RP, erwartete Datenpunkte"],
            ["2", "F3: Ingestion Pipeline", "PDF/XLS/HTML/TXT", "JSONL + TXT (validiert)"],
            ["3", sanitize("F1: Entity-Erkennung"), "JSONL-Dokument", sanitize("Verknuepfung mit Legal Entity")],
            ["4", "F4: Extraction Layer", "JSONL + Schema", "Strukturierte Fakten + Source-Refs"],
            ["5", "F5: Knowledge Graph", "Fakten", "Graph-Knoten + Kanten"],
            ["6", "F9: Inkonsistenz-Check", "Neuer Fakt", sanitize("Inkonsistenz-Flags")],
            ["7", "F7: Template-Update", "Neuer Fakt", "Snapshot + Delta"],
            ["8", "F6: Query Engine", "User-Abfrage", "Strukturierte Antwort"],
            ["9", "F8: Analyse", "Deltas + Muster", "Hypothesen + Trends"],
            ["10", "F11: Epistemik", "Antwort", "Konfidenz + Begruendung"],
        ],
        [18, 48, 48, 76]
    )

    # =========================================================================
    # 7. PHASEN
    # =========================================================================
    pdf.chapter_title("7. Umsetzungsphasen")

    pdf.section_title("Phase 1: Fundament (MVP)")
    pdf.add_simple_table(
        ["Feature", "Scope"],
        [
            ["F10", "Verzeichnis-Definitionen fuer alle Verzeichnisse"],
            ["F3", "Ingestion Pipeline (TXT-Passthrough + PDF -> JSONL+TXT)"],
            ["F1", "Legal Entity Management"],
            ["F4", "Geschlossene Extraktion (nur EOG-Beschluesse)"],
            ["F5", "Knowledge Graph (Kern-Ontologie)"],
            ["F6", "Query Engine (Structured Query, Basis-Aggregation)"],
        ],
        [25, 165]
    )
    pdf.body_text(sanitize(
        "Ergebnis: EOG-Beschluesse (3.RP + 4.RP) extrahiert, strukturiert, abfragbar. "
        "Einfache Vergleiche zwischen Netzbetreibern moeglich."
    ))

    pdf.section_title("Phase 2: Breite")
    pdf.add_simple_table(
        ["Feature", "Scope"],
        [
            ["F3+", sanitize("PDF-Ingestion Verbesserung, XLS-Support")],
            ["F4+", sanitize("Extraktion fuer Geschaeftsberichte + offene Extraktion")],
            ["F2", "Subject Matter Management"],
            ["F5+", "Ontologie-Erweiterung (Subject Matter als Dimension)"],
            ["F6+", "Semantic Search Fallback"],
        ],
        [25, 165]
    )
    pdf.body_text(sanitize(
        "Ergebnis: Alle Dokumenttypen extrahiert. Thematische Abfragen moeglich. "
        "Offene Extraktion liefert neue Ontologie-Kandidaten."
    ))

    pdf.section_title("Phase 3: Tiefe")
    pdf.add_simple_table(
        ["Feature", "Scope"],
        [
            ["F7", "Persistente Query-Templates + Snapshots + Deltas"],
            ["F9", sanitize("Inkonsistenz-Detektion (vollstaendig)")],
            ["F11", sanitize("Epistemische Bewertung (vollstaendig)")],
        ],
        [25, 165]
    )
    pdf.body_text(sanitize(
        "Ergebnis: System erkennt Widersprueche, bewertet Wissensqualitaet, trackt Veraenderungen."
    ))

    pdf.section_title("Phase 4: Intelligenz")
    pdf.add_simple_table(
        ["Feature", "Scope"],
        [
            ["F8", "Analyse & Prognose mit Hypothesen-Lifecycle"],
            ["F6+", sanitize("LLM-Reasoning fuer Synthese")],
            ["F3+", sanitize("Crawler fuer externe Quellen")],
            ["F7+", sanitize("Cross-Entity-Trend-Erkennung")],
        ],
        [25, 165]
    )
    pdf.body_text(sanitize(
        "Ergebnis: System generiert eigenstaendig Hypothesen, identifiziert Branchentrends, "
        "prognostiziert Regulierungsentwicklungen."
    ))

    # =========================================================================
    # 8. TECHNOLOGIE
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("8. Technologie-Empfehlungen")
    pdf.add_simple_table(
        ["Komponente", "Empfehlung", "Begruendung"],
        [
            ["Knowledge Graph", "Neo4j oder Apache AGE", "Graph-native Abfragen, Cypher"],
            ["Vektor-DB", "pgvector oder Qdrant", "Semantic Search Fallback"],
            ["LLM", "Claude / GPT-4 via API", "Extraktion + Reasoning"],
            ["Backend", "Python (FastAPI)", sanitize("ML/LLM-Oekosystem, async")],
            ["Datenformat", "JSONL + TXT parallel", "Verlustfrei + maschinenlesbar"],
            ["Task Queue", "Celery + Redis / Temporal", "Langlebige Extraktions-Jobs"],
        ],
        [40, 65, 85]
    )

    # =========================================================================
    # 9. OFFENE FRAGEN
    # =========================================================================
    pdf.chapter_title(sanitize("9. Offene Designfragen (Architekturphase)"))
    pdf.add_simple_table(
        ["Nr.", "Frage"],
        [
            ["1", "Graph-DB: Neo4j (dediziert) vs. Apache AGE (PostgreSQL-nativ)?"],
            ["2", sanitize("LLM-Strategie: Ein grosses Modell vs. spezialisierte kleinere?")],
            ["3", "Ontologie-Format: JSON-Schema vs. OWL/RDF vs. PropertyGraph-Schema?"],
            ["4", "UI/UX: Web-App vs. CLI-first vs. Notebook-first?"],
            ["5", "Multi-Tenancy: Single-Tenant vs. SaaS?"],
            ["6", sanitize("Embedding-Modell: Domain-specific Finetuning fuer Regulierungskontext?")],
        ],
        [15, 175]
    )

    # =========================================================================
    # 10. RISIKEN
    # =========================================================================
    pdf.chapter_title("10. Risiken & Mitigationen")
    pdf.add_simple_table(
        ["Risiko", "Wahrscheinlichkeit", "Impact", "Mitigation"],
        [
            [sanitize("OCR-Qualitaet unzureichend"), "Hoch", "Mittel", "Quality-Flags, Review-Queue"],
            ["LLM-Halluzination bei Zahlen", "Mittel", "Hoch", "Doppel-Extraktion, Regex-Validierung"],
            ["Ontologie zu starr", "Mittel", "Mittel", "Offene Extraktion + Feedback-Loop"],
            [sanitize("Context-Window zu klein"), "Hoch", "Mittel", "Sliding Window + Deduplizierung"],
            ["Skalierung", "Mittel", "Hoch", "Async Pipeline, Batch-Processing"],
        ],
        [50, 38, 27, 75]
    )

    # =========================================================================
    # GENERATE
    # =========================================================================
    output_path = os.path.join("D:", os.sep, "!_projects", "ngdai", "ngdai_produktkonzept.pdf")
    pdf.output(output_path)
    print(f"PDF erstellt: {output_path}")
    print(f"Seiten: {pdf.pages_count}")


if __name__ == "__main__":
    build_pdf()
