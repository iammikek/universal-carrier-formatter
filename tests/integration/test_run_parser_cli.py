"""
Integration tests for run_parser CLI (scripts/run_parser.py).

Invoke the Carrier Doc Parser script with a tiny PDF and mocked pipeline;
assert exit 0 and output JSON file exists with expected top-level keys (imp-11).
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.config import (
    KEY_CONSTRAINTS,
    KEY_EDGE_CASES,
    KEY_FIELD_MAPPINGS,
    KEY_GENERATOR_VERSION,
    KEY_SCHEMA,
    KEY_SCHEMA_VERSION,
)
from src.core.schema import Endpoint, HttpMethod, UniversalCarrierFormat


def _write_mock_output(output_path: str, schema: UniversalCarrierFormat) -> None:
    """Write minimal UCF-shaped JSON to output_path (as pipeline.process would)."""
    data = {
        KEY_SCHEMA_VERSION: "1.0.0",
        KEY_GENERATOR_VERSION: "test",
        KEY_SCHEMA: schema.model_dump(),
        KEY_FIELD_MAPPINGS: [],
        KEY_CONSTRAINTS: [],
        KEY_EDGE_CASES: [],
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


@pytest.mark.integration
class TestRunParserCLI:
    """Invoke run_parser script with mocked pipeline; assert output JSON."""

    def test_run_parser_cli_exit_zero_and_output_json_has_expected_keys(
        self, tmp_path: Path
    ) -> None:
        """
        Run run_parser.main() with mocked ExtractionPipeline; assert output file
        exists and has required top-level keys (schema, field_mappings, etc.).
        """
        pdf_file = tmp_path / "sample.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")
        output_file = tmp_path / "out_schema.json"

        mock_schema = UniversalCarrierFormat(
            name="RunParser CLI Test",
            base_url="https://api.test.com",
            endpoints=[
                Endpoint(
                    path="/api/track",
                    method=HttpMethod.GET,
                    summary="Track",
                )
            ],
        )

        def fake_process(pdf_path: str, output_path: str, **kwargs) -> None:
            _write_mock_output(output_path, mock_schema)

        mock_pipeline = MagicMock()
        mock_pipeline.process.side_effect = fake_process

        scripts_dir = Path(__file__).resolve().parent.parent.parent / "scripts"
        assert scripts_dir.is_dir(), "scripts dir not found"
        # Ensure fresh import so run_parser gets the patched ExtractionPipeline
        sys.modules.pop("run_parser", None)
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))

        with patch("src.extraction_pipeline.ExtractionPipeline") as MockPipeline:
            MockPipeline.return_value = mock_pipeline
            import run_parser as run_parser_module  # noqa: E402

            old_argv = sys.argv
            sys.argv = ["run_parser.py", str(pdf_file), "-o", str(output_file)]
            try:
                run_parser_module.main()
            finally:
                sys.argv = old_argv

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        required_keys = {
            KEY_SCHEMA_VERSION,
            KEY_GENERATOR_VERSION,
            KEY_SCHEMA,
            KEY_FIELD_MAPPINGS,
            KEY_CONSTRAINTS,
            KEY_EDGE_CASES,
        }
        for key in required_keys:
            assert key in data, f"Missing top-level key: {key}"
        assert data[KEY_SCHEMA]["name"] == "RunParser CLI Test"
        assert len(data[KEY_SCHEMA]["endpoints"]) == 1
        assert data[KEY_SCHEMA]["endpoints"][0]["path"] == "/api/track"
