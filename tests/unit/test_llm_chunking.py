"""
Unit tests for LLM chunking (imp-4): split and merge for very large PDFs.

Tests _split_text_into_chunks, _merge_schemas, _merge_field_mappings_lists,
_merge_lists_by_fingerprint, and LlmExtractorService chunking behaviour.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.llm_extractor import (
    LlmExtractorService,
    _merge_field_mappings_lists,
    _merge_lists_by_fingerprint,
    _merge_schemas,
    _split_text_into_chunks,
)


@pytest.mark.unit
class TestSplitTextIntoChunks:
    """Test _split_text_into_chunks."""

    def test_returns_single_chunk_when_under_limit(self):
        text = "short"
        assert _split_text_into_chunks(text, max_chars=100) == ["short"]

    def test_returns_single_chunk_when_empty(self):
        assert _split_text_into_chunks("", max_chars=10) == []
        assert _split_text_into_chunks("  \n  ", max_chars=10) == ["  \n  "]  # fallback

    def test_splits_on_paragraph_boundary(self):
        a = "a" * 50
        b = "b" * 50
        text = a + "\n\n" + b
        chunks = _split_text_into_chunks(text, max_chars=60, overlap_chars=0)
        assert len(chunks) == 2
        assert chunks[0] == a
        # Second chunk may have leading newline from boundary; content is preserved
        assert chunks[1].lstrip("\n") == b

    def test_splits_on_line_boundary_when_no_paragraph(self):
        lines = ["line" + str(i) for i in range(30)]
        text = "\n".join(lines)
        chunks = _split_text_into_chunks(text, max_chars=50, overlap_chars=0)
        assert len(chunks) >= 2
        for c in chunks:
            assert len(c) <= 50 + 10  # may include one extra newline

    def test_respects_max_chars(self):
        text = "x" * 200
        chunks = _split_text_into_chunks(text, max_chars=50, overlap_chars=0)
        assert len(chunks) >= 2
        for c in chunks:
            assert len(c) <= 51

    def test_overlap_reduces_gaps(self):
        text = "a\n\nb\n\nc\n\nd"
        chunks = _split_text_into_chunks(text, max_chars=4, overlap_chars=1)
        assert len(chunks) >= 2


@pytest.mark.unit
class TestMergeSchemas:
    """Test _merge_schemas."""

    def test_single_schema_returned_unchanged(self):
        from src.core.validator import CarrierValidator

        validator = CarrierValidator()
        data = {
            "name": "Carrier",
            "base_url": "https://api.example.com",
            "endpoints": [
                {"path": "/track", "method": "GET", "summary": "Track"},
            ],
        }
        schema = validator.validate(data)
        merged = _merge_schemas([schema])
        assert merged.name == schema.name
        assert len(merged.endpoints) == 1

    def test_merge_deduplicates_endpoints_by_path_method(self):
        from src.core.validator import CarrierValidator

        validator = CarrierValidator()
        base = {
            "name": "Carrier",
            "base_url": "https://api.example.com",
            "endpoints": [
                {"path": "/track", "method": "GET", "summary": "Track"},
            ],
        }
        s1 = validator.validate(base)
        base2 = {
            **base,
            "endpoints": [
                {"path": "/track", "method": "GET", "summary": "Track"},
                {"path": "/ship", "method": "POST", "summary": "Ship"},
            ],
        }
        s2 = validator.validate(base2)
        merged = _merge_schemas([s1, s2])
        assert merged.name == "Carrier"
        assert len(merged.endpoints) == 2
        paths = {e.path for e in merged.endpoints}
        assert "/track" in paths and "/ship" in paths


@pytest.mark.unit
class TestMergeFieldMappingsLists:
    """Test _merge_field_mappings_lists."""

    def test_deduplicates_by_carrier_and_universal_field(self):
        from src.core.config import KEY_CARRIER_FIELD, KEY_UNIVERSAL_FIELD

        a = [{KEY_CARRIER_FIELD: "trk", KEY_UNIVERSAL_FIELD: "tracking_number"}]
        b = [{KEY_CARRIER_FIELD: "trk", KEY_UNIVERSAL_FIELD: "tracking_number"}]
        merged = _merge_field_mappings_lists([a, b])
        assert len(merged) == 1
        assert merged[0][KEY_CARRIER_FIELD] == "trk"

    def test_keeps_different_mappings(self):
        from src.core.config import KEY_CARRIER_FIELD, KEY_UNIVERSAL_FIELD

        a = [{KEY_CARRIER_FIELD: "trk", KEY_UNIVERSAL_FIELD: "tracking_number"}]
        b = [{KEY_CARRIER_FIELD: "postcode", KEY_UNIVERSAL_FIELD: "postal_code"}]
        merged = _merge_field_mappings_lists([a, b])
        assert len(merged) == 2


@pytest.mark.unit
class TestMergeListsByFingerprint:
    """Test _merge_lists_by_fingerprint."""

    def test_deduplicates_by_content(self):
        a = [{"rule": "weight in grams"}]
        b = [{"rule": "weight in grams"}]
        merged = _merge_lists_by_fingerprint([a, b])
        assert len(merged) == 1

    def test_keeps_different_items(self):
        a = [{"rule": "weight in grams"}]
        b = [{"rule": "phone no + prefix"}]
        merged = _merge_lists_by_fingerprint([a, b])
        assert len(merged) == 2


@pytest.mark.unit
class TestLlmExtractorChunking:
    """Test LlmExtractorService uses chunking when text exceeds max_chars_per_chunk."""

    @patch("src.llm_extractor.get_chat_model")
    def test_extract_schema_chunks_when_text_exceeds_limit(self, mock_get_chat_model):
        """When text is longer than max_chars_per_chunk, extraction runs per chunk and merges."""
        mock_llm = MagicMock()
        mock_chain = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"name":"C","base_url":"https://x.com","endpoints":[{"path":"/a","method":"GET","summary":"A"},{"path":"/b","method":"POST","summary":"B"}]}'
        mock_chain.invoke.return_value = mock_response
        mock_prompt = MagicMock()
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)
        mock_get_chat_model.return_value = mock_llm

        with patch(
            "src.llm_extractor.get_schema_extraction_prompt", return_value=mock_prompt
        ):
            extractor = LlmExtractorService(
                api_key="test-key",
                max_chars_per_chunk=50,
            )
            # Text longer than 50 chars to trigger chunking
            long_text = "x" * 30 + "\n\n" + "y" * 30 + "\n\n" + "z" * 30

            schema = extractor.extract_schema(long_text)

        assert schema.name == "C"
        assert mock_chain.invoke.call_count >= 2
        assert len(schema.endpoints) >= 1
