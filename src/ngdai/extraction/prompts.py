"""Prompt-Templates fuer die geschlossene Faktenextraktion."""

# ── System Prompt (gleich fuer alle Dokumenttypen) ─────────

EXTRACTION_SYSTEM = """Du bist ein Experte fuer deutsche Energieregulierung. Deine Aufgabe ist es, strukturierte Datenpunkte aus regulatorischen Dokumenten zu extrahieren.

Regeln:
1. Extrahiere NUR Fakten die im Text explizit stehen. Erfinde NICHTS.
2. Fuer jeden Fakt: gib die Quelltextstelle an (woertliches Zitat, max 200 Zeichen).
3. Wenn ein Wert nicht im Text steht: setze value auf null.
4. Numerische Werte OHNE Tausender-Trennzeichen, Komma als Dezimaltrenner → Punkt umwandeln.
   Beispiel: "1.234.567,89 Euro" → 1234567.89
5. Prozentwerte als Dezimalzahl: "96,03%" → 96.03
6. Antworte ausschliesslich mit validem JSON, kein erklaerende Text."""


# ── EOG-Beschluesse ───────────────────────────────────────

EOG_USER_PROMPT = """Analysiere den folgenden EOG-Beschluss (Erlosobergrenze) der Bundesnetzagentur.

Extrahiere diese Datenpunkte:

**Periodenfix (einmal pro Regulierungsperiode):**
- effizienzwert: Ergebnis Effizienzvergleich in % (z.B. 96.03)
- ausgangsniveau: Kostenniveau/Ausgangsniveau in Euro
- verfahrensart: "vereinfachtes Verfahren" oder "Regelverfahren"
- basisjahr: Kostenbasis-Jahr (z.B. 2021)

**Jaehrlich variabel (pro Kalenderjahr):**
- eog_jahr: Kalenderjahreserloesobergrenzen - extrahiere ALLE Jahre als Array
  Format: [{{"jahr": 2024, "betrag": 12345678.90}}, ...]
- dnb_kosten: Dauerhaft nicht beeinflussbare Kosten in Euro (falls erwaehnt)

**Metadaten:**
- aktenzeichen: Aktenzeichen (z.B. "BK8-21-00148")
- netzbetreiber: Name des Netzbetreibers
- regulierungsperiode: z.B. "4. Regulierungsperiode" oder "3. Regulierungsperiode"
- sektor: "Strom" oder "Gas"
- beschlussdatum: Datum des Beschlusses

Antwort als JSON:
{{
  "metadaten": {{
    "aktenzeichen": "...",
    "netzbetreiber": "...",
    "regulierungsperiode": "...",
    "sektor": "...",
    "beschlussdatum": "..."
  }},
  "fakten": [
    {{
      "id": "effizienzwert",
      "value": 96.03,
      "unit": "%",
      "source_text": "woertliches Zitat aus dem Dokument",
      "confidence": 0.95
    }},
    ...
  ],
  "eog_jahreswerte": [
    {{"jahr": 2024, "betrag": 12345678.90, "source_text": "..."}},
    ...
  ]
}}

Dokument:
{text}"""


# ── Geschaeftsberichte ────────────────────────────────────

GB_USER_PROMPT = """Analysiere den folgenden Geschaeftsbericht eines deutschen Energieversorgers/Netzbetreibers.

Extrahiere diese Datenpunkte (Geschaeftsjahr, das im Bericht behandelt wird):

- gb_umsatz: Umsatzerloese in Euro
- gb_ebit: EBIT (Ergebnis vor Zinsen und Steuern) in Euro
- gb_mitarbeiter: Anzahl Mitarbeiter (Kopfzahl oder Vollzeitaequivalente)
- gb_investitionen: Investitionen/CAPEX in Euro
- gb_netzlaenge: Netzlaenge in km (falls erwaehnt)
- gb_anschlusspunkte: Anzahl Netzanschlusspunkte (falls erwaehnt)

**Metadaten:**
- unternehmen: Name des Unternehmens
- geschaeftsjahr: Jahr des Geschaeftsberichts (z.B. 2024)
- konzern_oder_einzelabschluss: "Konzern" oder "Einzelabschluss" oder "unklar"

Antwort als JSON:
{{
  "metadaten": {{
    "unternehmen": "...",
    "geschaeftsjahr": 2024,
    "konzern_oder_einzelabschluss": "..."
  }},
  "fakten": [
    {{
      "id": "gb_umsatz",
      "value": 123456789.00,
      "unit": "EUR",
      "source_text": "woertliches Zitat aus dem Dokument",
      "confidence": 0.9
    }},
    ...
  ]
}}

Wenn ein Wert nicht im Text vorkommt, lass ihn weg (nicht als null einfuegen).

Dokument:
{text}"""


def get_prompt_for_document_type(doc_type: str) -> tuple[str, str]:
    """Liefert (system_prompt, user_prompt) fuer einen Dokumenttyp.

    Raises:
        ValueError: Wenn kein Prompt fuer den Typ existiert.
    """
    prompts = {
        "eog": (EXTRACTION_SYSTEM, EOG_USER_PROMPT),
        "geschaeftsbericht": (EXTRACTION_SYSTEM, GB_USER_PROMPT),
    }
    if doc_type not in prompts:
        raise ValueError(f"Kein Extraktions-Prompt fuer Dokumenttyp '{doc_type}'. Verfuegbar: {list(prompts.keys())}")
    return prompts[doc_type]
