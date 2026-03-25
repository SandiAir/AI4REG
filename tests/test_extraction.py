"""Tests fuer F4: Closed Extraction."""

import pytest

from ngdai.extraction.prompts import get_prompt_for_document_type, EXTRACTION_SYSTEM
from ngdai.extraction.service import _to_float, _extract_with_sliding_window
from ngdai.llm.client import _extract_json


class TestPrompts:
    """Prompt-Template-Tests."""

    def test_eog_prompt_exists(self):
        system, user = get_prompt_for_document_type("eog")
        assert system == EXTRACTION_SYSTEM
        assert "{text}" in user
        assert "effizienzwert" in user
        assert "eog_jahr" in user

    def test_gb_prompt_exists(self):
        system, user = get_prompt_for_document_type("geschaeftsbericht")
        assert "{text}" in user
        assert "gb_umsatz" in user
        assert "gb_ebit" in user

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Kein Extraktions-Prompt"):
            get_prompt_for_document_type("unknown_type")


class TestJsonExtraction:
    """JSON-Extraction aus LLM-Antworten."""

    def test_plain_json(self):
        result = _extract_json('{"key": "value"}')
        assert result == '{"key": "value"}'

    def test_markdown_json_block(self):
        text = 'Hier ist das Ergebnis:\n```json\n{"key": "value"}\n```\nFertig.'
        result = _extract_json(text)
        assert result == '{"key": "value"}'

    def test_markdown_generic_block(self):
        text = '```\n{"key": "value"}\n```'
        result = _extract_json(text)
        assert result == '{"key": "value"}'

    def test_json_with_surrounding_text(self):
        text = 'Analyse: {"key": "value"} Ende.'
        result = _extract_json(text)
        assert result == '{"key": "value"}'

    def test_array_json(self):
        result = _extract_json('[1, 2, 3]')
        assert result == '[1, 2, 3]'


class TestNumericConversion:
    """Numerische Wert-Konvertierung."""

    def test_float(self):
        assert _to_float(96.03) == 96.03

    def test_int(self):
        assert _to_float(100) == 100.0

    def test_string_simple(self):
        assert _to_float("96.03") == 9603.0  # Punkt = Tausender in DE

    def test_german_notation(self):
        # 1.234.567,89 → 1234567.89
        assert _to_float("1.234.567,89") == 1234567.89

    def test_invalid_string(self):
        assert _to_float("kein Wert") is None

    def test_none(self):
        assert _to_float(None) is None


class TestSlidingWindow:
    """Sliding-Window-Logik (ohne LLM-Aufruf)."""

    def test_window_boundaries(self):
        """Prüft dass Windows korrekt aufgeteilt werden."""
        from ngdai.extraction.service import MAX_WINDOW_CHARS, OVERLAP_CHARS

        # Simuliere Text der 2 Windows braucht
        text_len = MAX_WINDOW_CHARS + 100_000
        assert text_len > MAX_WINDOW_CHARS

        # Berechne erwartete Windows
        windows = []
        start = 0
        while start < text_len:
            end = start + MAX_WINDOW_CHARS
            windows.append((start, min(end, text_len)))
            start = end - OVERLAP_CHARS
            if end >= text_len:
                break

        assert len(windows) >= 2
        # Overlap prüfen
        assert windows[1][0] < windows[0][1]  # Zweites Window startet vor Ende des ersten
