"""Tests für den LLM-Extractor."""

import json
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from core.llm_extractor import _load_prompt, _parse_json_response, extract_from_text
from core.models import ExtractedPosition, ExtractionResult


@pytest.fixture(autouse=True)
def _clear_prompt_cache():
    """Prompt-Cache vor jedem Test leeren."""
    import core.llm_extractor as llm_extractor

    llm_extractor._PROMPT_CACHE = None
    yield
    llm_extractor._PROMPT_CACHE = None


def _make_chat_response(positions, document_type="Kaufvertrag", overall_confidence=0.9):
    payload = {
        "extracted_positions": positions,
        "parties": [],
        "document_type": document_type,
        "overall_confidence": overall_confidence,
        "notes": "",
    }
    return type(
        "Response", (), {"message": type("Message", (), {"content": json.dumps(payload)})()}
    )()


class TestExtractFromText:
    @pytest.fixture(autouse=True)
    def _mock_load_prompt(self, mocker: MockerFixture):
        mocker.patch("core.llm_extractor._load_prompt", return_value="Test system prompt")

    def test_successful_extraction(self, mocker: MockerFixture):
        mock_client_cls = mocker.patch("core.llm_extractor.ollama.Client")
        mock_client = mock_client_cls.return_value
        mock_client.chat.return_value = _make_chat_response(
            [
                {
                    "kv_number": "21200",
                    "description": "Beurkundung",
                    "business_value_eur": 450000.0,
                    "source_reference": "Seite 2",
                    "confidence": 0.95,
                    "reasoning": "Hauptkaufvertrag",
                }
            ]
        )

        result = extract_from_text("Urkundentext", model="test-model", temperature=0.1)

        assert isinstance(result, ExtractionResult)
        assert len(result.extracted_positions) == 1
        pos = result.extracted_positions[0]
        assert isinstance(pos, ExtractedPosition)
        assert pos.kv_number == "21200"
        assert pos.business_value_eur == 450000.0
        assert pos.confidence == 0.95
        mock_client_cls.assert_called_once()
        mock_client.chat.assert_called_once()

    def test_low_confidence_is_filtered(self, mocker: MockerFixture):
        mock_client_cls = mocker.patch("core.llm_extractor.ollama.Client")
        mock_client = mock_client_cls.return_value
        mock_client.chat.return_value = _make_chat_response(
            [
                {
                    "kv_number": "21200",
                    "description": "Beurkundung",
                    "business_value_eur": 100000.0,
                    "source_reference": "Seite 1",
                    "confidence": 0.1,
                    "reasoning": "Unsicher",
                }
            ]
        )

        result = extract_from_text("Urkundentext")

        assert len(result.extracted_positions) == 0

    def test_unknown_kv_number_accepted(self, mocker: MockerFixture):
        mock_client_cls = mocker.patch("core.llm_extractor.ollama.Client")
        mock_client = mock_client_cls.return_value
        mock_client.chat.return_value = _make_chat_response(
            [
                {
                    "kv_number": "99999",
                    "description": "Sonderleistung",
                    "business_value_eur": 1000.0,
                    "source_reference": "Seite 1",
                    "confidence": 0.8,
                    "reasoning": "Manuell prüfen",
                }
            ]
        )

        result = extract_from_text("Urkundentext")

        assert len(result.extracted_positions) == 1
        assert result.extracted_positions[0].kv_number == "99999"

    def test_invalid_position_skipped(self, mocker: MockerFixture):
        mock_client_cls = mocker.patch("core.llm_extractor.ollama.Client")
        mock_client = mock_client_cls.return_value
        mock_client.chat.return_value = _make_chat_response(
            [
                {
                    "kv_number": "21200",
                    "description": "Beurkundung",
                    "business_value_eur": 1000.0,
                    "source_reference": "Seite 1",
                    "confidence": "kein-float",
                    "reasoning": "",
                }
            ]
        )

        result = extract_from_text("Urkundentext")

        assert len(result.extracted_positions) == 0

    def test_json_decode_error_retries_and_fails(self, mocker: MockerFixture):
        mock_client_cls = mocker.patch("core.llm_extractor.ollama.Client")
        mock_client = mock_client_cls.return_value
        mock_client.chat.return_value = type(
            "Response", (), {"message": type("Message", (), {"content": "Kein JSON"})()}
        )()

        with pytest.raises(RuntimeError, match="kein gültiges Ergebnis"):
            extract_from_text("Urkundentext", max_retries=1)

        assert mock_client.chat.call_count == 2

    def test_ollama_connection_refused(self, mocker: MockerFixture):
        mock_client_cls = mocker.patch("core.llm_extractor.ollama.Client")
        mock_client = mock_client_cls.return_value
        mock_client.chat.side_effect = Exception("Connection refused")

        with pytest.raises(RuntimeError, match="Ollama ist nicht erreichbar"):
            extract_from_text("Urkundentext")


class TestParseJsonResponse:
    def test_plain_json(self):
        raw = '{"a": 1}'
        assert _parse_json_response(raw) == {"a": 1}

    def test_markdown_codeblock(self):
        raw = '```json\n{"a": 1}\n```'
        assert _parse_json_response(raw) == {"a": 1}

    def test_json_with_surrounding_text(self):
        raw = 'Hier ist das Ergebnis: {"a": 1} Ende'
        assert _parse_json_response(raw) == {"a": 1}


class TestLoadPrompt:
    def test_invalid_version_raises(self):
        with pytest.raises(ValueError, match="Ungültige Prompt-Version"):
            _load_prompt("../etc/passwd")

    def test_valid_version_reads_file(self, tmp_path):
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        prompt_file = prompts_dir / "extraction_v1.txt"
        prompt_file.write_text("Dummy prompt", encoding="utf-8")

        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)
            assert _load_prompt("v1") == "Dummy prompt"
        finally:
            os.chdir(original_cwd)

    def test_missing_file_returns_empty(self, tmp_path):
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)
            assert _load_prompt("v1") == ""
        finally:
            os.chdir(original_cwd)
