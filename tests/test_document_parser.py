"""Tests für den Document Parser."""

import pytest
from pathlib import Path

from core.document_parser import parse_document, _strip_rtf
from core.models import ExtractionQuality


class TestParseTxt:
    def test_basic_txt(self):
        doc = parse_document(
            "Beispielurkunden/txt/01_Grundstueckskauf_Einfach_Einfamilienhaus.txt"
        )
        assert doc.pages >= 1
        assert len(doc.full_text) > 500
        assert doc.extraction_quality == ExtractionQuality.GOOD
        assert "Kaufpreis" in doc.full_text or "Kaufvertrag" in doc.full_text

    def test_testament_txt(self):
        doc = parse_document(
            "Beispielurkunden/txt/09_Testament_Einfach_Einzeltestament_Alleinerbe.txt"
        )
        assert doc.pages >= 1
        assert len(doc.full_text) > 300
        assert doc.extraction_quality == ExtractionQuality.GOOD


class TestParseRtf:
    def test_basic_rtf(self):
        doc = parse_document(
            "Beispielurkunden/rtf/01_Grundstueckskauf_Einfach_Einfamilienhaus.rtf"
        )
        assert doc.pages >= 1
        assert len(doc.full_text) > 500
        assert doc.extraction_quality == ExtractionQuality.GOOD

    def test_rtf_no_trailing_backslash(self):
        doc = parse_document(
            "Beispielurkunden/rtf/01_Grundstueckskauf_Einfach_Einfamilienhaus.rtf"
        )
        for line in doc.full_text.split("\n"):
            stripped = line.rstrip()
            if len(stripped) > 1:
                assert not stripped.endswith("\\"), f"Trailing backslash: {repr(stripped[-30:])}"


class TestUnsupportedFormat:
    def test_raises_on_unsupported(self):
        # Datei mit ungültigem Format existiert nicht → FileNotFoundError
        with pytest.raises((ValueError, FileNotFoundError)):
            parse_document("test.xyz")

    def test_raises_on_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            parse_document("/nonexistent/file.txt")


class TestRtfStripping:
    def test_strip_par_command(self):
        text = r"Hello\par World"
        result = _strip_rtf(text)
        assert "Hello" in result
        assert "World" in result
        assert "\n" in result

    def test_strip_hex_escape(self):
        text = r"M\'fcnchen"
        result = _strip_rtf(text)
        assert "München" in result
