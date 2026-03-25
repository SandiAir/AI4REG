"""Tests fuer F5/F6: Knowledge Graph + Query Engine."""

import pytest

from ngdai.query.service import (
    _detect_fact_type,
    _extract_entity_name,
    _is_comparison_query,
    _is_aggregation_query,
    _clean_entity_part,
)
from ngdai.graph.service import _escape


class TestQueryRouting:
    """Query-Typ-Erkennung."""

    def test_comparison_vs(self):
        assert _is_comparison_query("elmshorn vs albwerk")

    def test_comparison_gegen(self):
        assert _is_comparison_query("elmshorn gegen albwerk")

    def test_not_comparison(self):
        assert not _is_comparison_query("effizienzwert stadtwerke elmshorn")

    def test_aggregation_median(self):
        assert _is_aggregation_query("median effizienzwert 4.rp strom")

    def test_aggregation_durchschnitt(self):
        assert _is_aggregation_query("durchschnitt eog 3.rp")

    def test_not_aggregation(self):
        assert not _is_aggregation_query("effizienzwert stadtwerke elmshorn")


class TestFactTypeDetection:
    """Erkennung des Fakt-Typs aus Fragen."""

    def test_effizienzwert(self):
        assert _detect_fact_type("Effizienzwert Stadtwerke Elmshorn") == "effizienzwert"

    def test_eog(self):
        assert _detect_fact_type("EOG 4.RP Stadtwerke Elmshorn") == "eog_jahr"

    def test_umsatz(self):
        assert _detect_fact_type("Umsatz EnBW 2024") == "gb_umsatz"

    def test_ebit(self):
        assert _detect_fact_type("EBIT N-ERGIE") == "gb_ebit"

    def test_unknown(self):
        assert _detect_fact_type("Was ist der Sinn des Lebens?") is None


class TestEntityNameExtraction:
    """Entity-Name aus Frage extrahieren."""

    def test_basic(self):
        name = _extract_entity_name("Effizienzwert Stadtwerke Elmshorn", "effizienzwert")
        assert name is not None
        assert "Stadtwerke" in name
        assert "Elmshorn" in name

    def test_with_dimensions(self):
        name = _extract_entity_name("EOG 4.RP Strom Albwerk", "eog_jahr")
        assert name is not None
        assert "Albwerk" in name

    def test_too_short(self):
        name = _extract_entity_name("Effizienzwert", "effizienzwert")
        assert name is None


class TestEntityPartCleaning:
    """Bereinigung von Entity-Teilen in Vergleichsfragen."""

    def test_removes_keywords(self):
        result = _clean_entity_part("Stadtwerke Elmshorn EOG 4.RP")
        assert "Stadtwerke Elmshorn" in result
        assert "EOG" not in result


class TestGraphHelpers:
    """Graph-Hilfsfunktionen."""

    def test_escape_single_quotes(self):
        assert _escape("O'Brien") == "O\\'Brien"

    def test_escape_no_quotes(self):
        assert _escape("Normal Text") == "Normal Text"
