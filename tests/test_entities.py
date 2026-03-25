"""Tests fuer F1: Legal Entity Management."""

import csv
import tempfile
from pathlib import Path

import pytest

from ngdai.entities.service import (
    parse_aktenzeichen,
    _AZ_WITH_NAME_PATTERN,
)


class TestAktenzeichenParser:
    """Aktenzeichen-Erkennung aus Text."""

    def test_parse_standard_bk8(self):
        result = parse_aktenzeichen("Beschluss BK8-21-00148 vom 15.12.2023")
        assert result == ["BK8-21-00148"]

    def test_parse_standard_bk9(self):
        result = parse_aktenzeichen("Beschluss BK9-22-00032 Gas")
        assert result == ["BK9-22-00032"]

    def test_parse_multiple(self):
        text = "BK8-21-00148 und BK8-21-00260 und BK9-22-00032"
        result = parse_aktenzeichen(text)
        assert len(result) == 3

    def test_parse_with_dash_variants(self):
        result = parse_aktenzeichen("BK8–21–00148")  # En-Dash
        assert result == ["BK8-21-00148"]  # Normalisiert

    def test_parse_with_spaces(self):
        result = parse_aktenzeichen("BK8 - 21 - 00148")
        assert result == ["BK8-21-00148"]

    def test_parse_no_match(self):
        result = parse_aktenzeichen("Kein Aktenzeichen hier")
        assert result == []

    def test_parse_deduplication(self):
        text = "BK8-21-00148 wird in BK8-21-00148 erwaehnt"
        result = parse_aktenzeichen(text)
        assert len(result) == 1

    def test_az_with_name_pattern(self):
        text = "BK8-21-00148 - Stadtwerke Elmshorn GmbH\n"
        match = _AZ_WITH_NAME_PATTERN.search(text)
        assert match is not None
        assert "Stadtwerke Elmshorn GmbH" in match.group(1)


class TestCSVFormat:
    """Stellt sicher, dass wir das MaStR-CSV-Format korrekt parsen."""

    def test_semicolon_csv_round_trip(self, tmp_path):
        """Schreibt eine Test-CSV und prüft ob sie korrekt gelesen wird."""
        csv_file = tmp_path / "test_strom.csv"
        header = [
            "MaStR-Nr.", "Name des Marktakteurs", "Marktfunktion",
            "Marktrollen", "Bundesland", "Postleitzahl", "Ort",
            "Straße", "Hausnummer", "Land", "Registrierungsdatum",
            "Datum der letzten Aktualisierung", "ACER-Code",
            "Geschlossenes Verteilernetz", "Tätigkeitsstatus",
            "Tätigkeitsbeginn", "Tätigkeitsende",
        ]
        rows = [
            {
                "MaStR-Nr.": "SNB982046657236",
                "Name des Marktakteurs": "50Hertz Transmission GmbH",
                "Marktfunktion": "Stromnetzbetreiber",
                "Marktrollen": "Anschlussnetzbetreiber, Übertragungsnetzbetreiber",
                "Bundesland": "Berlin",
                "Postleitzahl": "10557",
                "Ort": "Berlin",
                "Straße": "Heidestraße",
                "Hausnummer": "2",
                "Land": "Deutschland",
                "Registrierungsdatum": "14.6.2017",
                "Datum der letzten Aktualisierung": "17.9.2024",
                "ACER-Code": "A00014369.DE",
                "Geschlossenes Verteilernetz": "Nein",
                "Tätigkeitsstatus": "Aktiv",
                "Tätigkeitsbeginn": "1.1.2008",
                "Tätigkeitsende": "",
            },
        ]

        # BOM + Semikolon wie das echte Format
        with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=header, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(rows)

        # Lesen wie der Import es tut
        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";", quotechar='"')
            parsed = list(reader)

        assert len(parsed) == 1
        assert parsed[0]["MaStR-Nr."] == "SNB982046657236"
        assert parsed[0]["Name des Marktakteurs"] == "50Hertz Transmission GmbH"
        assert "Übertragungsnetzbetreiber" in parsed[0]["Marktrollen"]
