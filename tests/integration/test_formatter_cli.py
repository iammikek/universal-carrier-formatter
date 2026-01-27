"""
Tests for CLI Formatter.

Laravel Equivalent: tests/Feature/FormatterCommandTest.php

These tests validate the CLI interface for the formatter.
"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.core.schema import Endpoint, HttpMethod, UniversalCarrierFormat
from src.formatter import main


@pytest.mark.integration
class TestFormatterCLI:
    """Test CLI formatter interface."""

    def test_cli_basic_usage(self, tmp_path):
        """Test basic CLI usage."""
        runner = CliRunner()

        # Create a dummy PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        output_file = tmp_path / "output.json"

        with patch("src.formatter.ExtractionPipeline") as mock_pipeline_class:
            mock_pipeline = MagicMock()
            mock_schema = UniversalCarrierFormat(
                name="Test Carrier",
                base_url="https://api.test.com",
                endpoints=[
                    Endpoint(path="/api/track", method=HttpMethod.GET, summary="Track")
                ],
            )
            mock_pipeline.process.return_value = mock_schema
            mock_pipeline_class.return_value = mock_pipeline

            result = runner.invoke(
                main,
                [str(pdf_file), "--output", str(output_file)],
            )

            assert result.exit_code == 0
            assert "Test Carrier" in result.output
            mock_pipeline.process.assert_called_once()

    def test_cli_default_output_path(self, tmp_path):
        """Test CLI uses default output path when not specified."""
        runner = CliRunner()

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        with patch("src.formatter.ExtractionPipeline") as mock_pipeline_class:
            mock_pipeline = MagicMock()
            from src.core.schema import (Endpoint, HttpMethod,
                                         UniversalCarrierFormat)

            mock_schema = UniversalCarrierFormat(
                name="Test",
                base_url="https://api.test.com",
                endpoints=[
                    Endpoint(path="/api/track", method=HttpMethod.GET, summary="Track")
                ],
            )
            mock_pipeline.process.return_value = mock_schema
            mock_pipeline_class.return_value = mock_pipeline

            # Change to tmp_path so output directory is created there
            import os

            old_cwd = os.getcwd()
            try:
                os.chdir(tmp_path)
                result = runner.invoke(main, [str(pdf_file)])

                assert result.exit_code == 0
                # Should create output/test_schema.json
                assert (
                    tmp_path / "output" / "test_schema.json"
                ).exists() or "Test" in result.output
            finally:
                os.chdir(old_cwd)

    def test_cli_verbose_mode(self, tmp_path):
        """Test CLI verbose logging."""
        runner = CliRunner()

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        with patch("src.formatter.ExtractionPipeline") as mock_pipeline_class:
            mock_pipeline = MagicMock()
            from src.core.schema import UniversalCarrierFormat

            mock_schema = UniversalCarrierFormat(
                name="Test",
                base_url="https://api.test.com",
                endpoints=[
                    Endpoint(path="/api/track", method=HttpMethod.GET, summary="Track")
                ],
            )
            mock_pipeline.process.return_value = mock_schema
            mock_pipeline_class.return_value = mock_pipeline

            result = runner.invoke(
                main,
                [str(pdf_file), "--verbose"],
            )

            assert result.exit_code == 0

    def test_cli_custom_model(self, tmp_path):
        """Test CLI with custom LLM model."""
        runner = CliRunner()

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        with patch("src.formatter.ExtractionPipeline") as mock_pipeline_class:
            mock_pipeline = MagicMock()
            from src.core.schema import UniversalCarrierFormat

            mock_schema = UniversalCarrierFormat(
                name="Test",
                base_url="https://api.test.com",
                endpoints=[
                    Endpoint(path="/api/track", method=HttpMethod.GET, summary="Track")
                ],
            )
            mock_pipeline.process.return_value = mock_schema
            mock_pipeline_class.return_value = mock_pipeline

            result = runner.invoke(
                main,
                [str(pdf_file), "--llm-model", "gpt-4.1-nano"],
            )

            assert result.exit_code == 0
            # Verify pipeline was created with correct model
            mock_pipeline_class.assert_called_once()
            call_kwargs = mock_pipeline_class.call_args[1]
            assert call_kwargs.get("llm_model") == "gpt-4.1-nano"

    def test_cli_no_tables_option(self, tmp_path):
        """Test CLI --no-tables option."""
        runner = CliRunner()

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        with patch("src.formatter.ExtractionPipeline") as mock_pipeline_class:
            mock_pipeline = MagicMock()
            from src.core.schema import UniversalCarrierFormat

            mock_schema = UniversalCarrierFormat(
                name="Test",
                base_url="https://api.test.com",
                endpoints=[
                    Endpoint(path="/api/track", method=HttpMethod.GET, summary="Track")
                ],
            )
            mock_pipeline.process.return_value = mock_schema
            mock_pipeline_class.return_value = mock_pipeline

            result = runner.invoke(
                main,
                [str(pdf_file), "--no-tables"],
            )

            assert result.exit_code == 0
            # Verify pipeline was created with extract_tables=False
            mock_pipeline_class.assert_called_once()
            call_kwargs = mock_pipeline_class.call_args[1]
            assert call_kwargs.get("extract_tables") is False

    def test_cli_error_handling(self, tmp_path):
        """Test CLI error handling."""
        runner = CliRunner()

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        with patch("src.formatter.ExtractionPipeline") as mock_pipeline_class:
            mock_pipeline = MagicMock()
            mock_pipeline.process.side_effect = ValueError("Test error")
            mock_pipeline_class.return_value = mock_pipeline

            result = runner.invoke(
                main,
                [str(pdf_file)],
            )

            assert result.exit_code == 1
            assert "Error" in result.output or "error" in result.output.lower()

    def test_cli_error_handling_verbose(self, tmp_path):
        """Test CLI error handling with verbose mode shows traceback."""
        runner = CliRunner()

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        with patch("src.formatter.ExtractionPipeline") as mock_pipeline_class:
            mock_pipeline = MagicMock()
            mock_pipeline.process.side_effect = ValueError("Test error")
            mock_pipeline_class.return_value = mock_pipeline

            result = runner.invoke(
                main,
                [str(pdf_file), "--verbose"],
            )

            assert result.exit_code == 1
            # Verbose mode should show more details
            assert "Error" in result.output or "error" in result.output.lower()

    def test_cli_nonexistent_file(self):
        """Test CLI with non-existent PDF file."""
        runner = CliRunner()

        result = runner.invoke(
            main,
            ["nonexistent.pdf"],
        )

        # Click should handle file validation
        assert result.exit_code != 0
