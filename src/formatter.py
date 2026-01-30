#!/usr/bin/env python3
"""
CLI Entry Point - Universal Carrier Formatter.

Main CLI interface for the Universal Carrier Formatter.
It orchestrates the complete pipeline: PDF → LLM → Universal Schema.

Usage:
    python -m src.formatter examples/dhl_express_api_docs.pdf --output output/schema.json
"""

import logging
import sys
import time
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

from .core.config import (
    DEFAULT_LLM_MODEL,
    STEP_EXTRACT,
    STEP_PARSE,
    STEP_SAVE,
    STEP_VALIDATE,
)
from .extraction_pipeline import ExtractionPipeline

# Load environment variables from .env file
load_dotenv()

# Set up logging (suppress for cleaner CLI output)
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings/errors in CLI
    format="%(message)s",
)


@click.command()
@click.argument("input", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output JSON file path (default: output/{carrier_name}_schema.json)",
)
@click.option(
    "--llm-model",
    default=None,
    help=f"LLM model (default: provider-specific, e.g. {DEFAULT_LLM_MODEL})",
)
@click.option(
    "--provider",
    type=click.Choice(["openai", "anthropic", "azure"], case_sensitive=False),
    default=None,
    help="LLM provider: openai, anthropic, or azure (default: LLM_PROVIDER env or openai)",
)
@click.option(
    "--no-tables",
    is_flag=True,
    help="Don't extract tables from PDF",
)
@click.option(
    "--no-validators",
    is_flag=True,
    help="Don't write Pydantic validator code from constraints (Scenario 2)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed processing logs",
)
@click.option(
    "--dump-pdf-text",
    "dump_pdf_text_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Write extracted PDF text to FILE (exact text sent to the LLM). Use '.' for output/<input_stem>_pdf_text.txt.",
)
@click.option(
    "--extracted-text",
    "extracted_text_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Use FILE as the text sent to the LLM instead of extracting from the PDF. Skips PDF parsing.",
)
@click.option(
    "--dry-run",
    "dry_run",
    is_flag=True,
    help="Extract PDF text only; write to file and exit without calling the LLM. Use --dump-pdf-text or default output/<stem>_pdf_text.txt.",
)
def main(
    input: Path,
    output: Optional[Path],
    llm_model: Optional[str],
    provider: Optional[str],
    no_tables: bool,
    no_validators: bool,
    verbose: bool,
    dump_pdf_text_path: Optional[Path],
    extracted_text_path: Optional[Path],
    dry_run: bool,
) -> None:
    """
    Extract Universal Carrier Format schema from carrier API documentation PDF.

    INPUT: Path to PDF file containing carrier API documentation

    Example:
        python -m src.formatter examples/dhl_express_api_docs.pdf --output output/dhl_schema.json
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        # Show all logs in verbose mode
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            force=True,
        )

    start_time = time.time()

    click.echo("=" * 70)
    click.echo("Universal Carrier Formatter")
    click.echo("=" * 70)
    click.echo()

    # Determine output path
    if output is None:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output = output_dir / f"{input.stem}_schema.json"

    try:
        # Initialize pipeline
        click.echo("🔧 Initializing extraction pipeline...")
        click.echo(f"   Provider: {provider or 'openai'}")
        click.echo(f"   Model: {llm_model or '(default for provider)'}")
        click.echo(f"   Extract tables: {not no_tables}")
        click.echo()

        pipeline = ExtractionPipeline(
            llm_model=llm_model,
            extract_tables=not no_tables,
            provider=provider,
        )

        if dry_run:
            # PDF → text only; no LLM (imp-26)
            if dump_pdf_text_path and str(dump_pdf_text_path).strip() != ".":
                text_out = Path(dump_pdf_text_path)
            else:
                text_out = output.parent / f"{input.stem}_pdf_text.txt"
            click.echo("📄 Dry-run: extracting PDF text only (no LLM)...")
            click.echo(f"   Input: {input}")
            click.echo(f"   Text output: {text_out}")
            click.echo()
            pipeline.extract_text_only(
                str(input),
                output_path=str(text_out),
                progress_callback=_progress_callback,
            )
            click.echo()
            click.echo("✅ Dry-run complete. Text written to:", text_out)
            return

        # Process PDF with progress feedback
        click.echo("📄 Processing...")
        click.echo(f"   Input: {input}")
        click.echo(f"   Output: {output}")
        if extracted_text_path:
            click.echo(
                f"   Using extracted text: {extracted_text_path} (skipping PDF parse)"
            )
        dump_path = None
        if dump_pdf_text_path and not extracted_text_path:
            dump_path = (
                output.parent / f"{input.stem}_pdf_text.txt"
                if str(dump_pdf_text_path).strip() == "."
                else dump_pdf_text_path
            )
            click.echo(f"   Dump PDF text: {dump_path}")
        click.echo()

        schema = pipeline.process(
            str(input),
            str(output),
            progress_callback=_progress_callback,
            generate_validators=not no_validators,
            dump_pdf_text_path=str(dump_path) if dump_path else None,
            extracted_text_path=(
                str(extracted_text_path) if extracted_text_path else None
            ),
        )

        elapsed = time.time() - start_time

        click.echo()
        click.echo("=" * 70)
        click.echo("✅ Extraction Complete!")
        click.echo("=" * 70)
        click.echo(f"📦 Carrier: {schema.name}")
        click.echo(f"🌐 Base URL: {schema.base_url}")
        click.echo(f"🔗 Endpoints: {len(schema.endpoints)}")
        if schema.authentication:
            click.echo(f"🔐 Authentication: {len(schema.authentication)} method(s)")
        if schema.rate_limits:
            click.echo(f"⏱️  Rate Limits: {len(schema.rate_limits)} limit(s)")
        click.echo(f"💾 Output: {output}")
        click.echo(f"⏱️  Time: {elapsed:.1f}s")
        click.echo()

    except KeyboardInterrupt:
        click.echo()
        click.echo("❌ Interrupted by user", err=True)
        sys.exit(1)
    except (ValueError, OSError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo()
        click.echo("=" * 70)
        click.echo("❌ Error", err=True)
        click.echo("=" * 70, err=True)
        click.echo(f"   {e}", err=True)
        click.echo()
        if verbose:
            import traceback

            click.echo("Full traceback:", err=True)
            traceback.print_exc()
        else:
            click.echo("   Run with --verbose for more details", err=True)
        click.echo()
        sys.exit(1)


def _progress_callback(step: str, message: str = "") -> None:
    """
    Progress callback for extraction pipeline.

    Args:
        step: Current step name
        message: Optional message
    """
    step_icons = {
        STEP_PARSE: "📖",
        STEP_EXTRACT: "🤖",
        STEP_VALIDATE: "✅",
        STEP_SAVE: "💾",
    }
    icon = step_icons.get(step, "⏳")

    if message:
        click.echo(f"{icon} {step.capitalize()}: {message}")
    else:
        click.echo(f"{icon} {step.capitalize()}...")


if __name__ == "__main__":
    main()
