"""Tests fuer F3: Ingestion Pipeline."""

import pytest

from ngdai.ingestion.service import (
    _guess_document_type,
    _guess_sector,
    _read_text_file,
)


class TestDocumentTypeGuessing:
    """Dokumenttyp-Erkennung aus Pfad."""

    def test_eog_from_path(self):
        assert _guess_document_type("dritteregulierung/EOG/BK8-21-00148.txt") == "eog"

    def test_geschaeftsbericht_from_path(self):
        assert _guess_document_type("Geschäftsberichte/2024/test.txt") == "geschaeftsbericht"

    def test_festlegung_from_path(self):
        assert _guess_document_type("dritteregulierung/festlegung/test.txt") == "festlegung"

    def test_unknown_from_path(self):
        assert _guess_document_type("random/path/file.txt") == "unknown"


class TestSectorGuessing:
    """Sektor-Erkennung aus Pfad."""

    def test_strom_from_bk8(self):
        assert _guess_sector("EOG/BK8-21-00148.txt") == "strom"

    def test_gas_from_bk9(self):
        assert _guess_sector("EOG/BK9-22-00032.txt") == "gas"

    def test_empty_for_unknown(self):
        assert _guess_sector("some/random/path.txt") == ""


class TestTextFileReading:
    """TXT-Lesen mit Encoding-Fallback."""

    def test_read_utf8(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hallo Welt äöü", encoding="utf-8")
        assert _read_text_file(f) == "Hallo Welt äöü"

    def test_read_latin1(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_bytes("Hallo Welt \xe4\xf6\xfc".encode("latin-1"))
        result = _read_text_file(f)
        assert result is not None
        assert "Hallo Welt" in result

    def test_read_bom(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("BOM Test", encoding="utf-8-sig")
        result = _read_text_file(f)
        assert "BOM Test" in result
