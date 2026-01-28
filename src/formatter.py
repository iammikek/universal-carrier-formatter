#!/usr/bin/env python3
"""
CLI Entry Point - Universal Carrier Formatter

Laravel Equivalent: app/Console/Commands/FormatCarrier.php

This is the main CLI interface for the Universal Carrier Formatter.
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
    default="gpt-4.1-mini",
    help="LLM model to use (default: gpt-4.1-mini - under $2.5/1M tokens)",
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
def main(
    input: Path,
    output: Path,
    llm_model: str,
    no_tables: bool,
    no_validators: bool,
    verbose: bool,
    dump_pdf_text_path: Optional[Path],
    extracted_text_path: Optional[Path],
):
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
        click.echo(f"   Model: {llm_model}")
        click.echo(f"   Extract tables: {not no_tables}")
        click.echo()

        pipeline = ExtractionPipeline(llm_model=llm_model, extract_tables=not no_tables)

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


def _progress_callback(step: str, message: str = ""):
    """
    Progress callback for extraction pipeline.

    Args:
        step: Current step name
        message: Optional message
    """
    step_icons = {
        "parse": "📖",
        "extract": "🤖",
        "validate": "✅",
        "save": "💾",
    }
    icon = step_icons.get(step, "⏳")

    if message:
        click.echo(f"{icon} {step.capitalize()}: {message}")
    else:
        click.echo(f"{icon} {step.capitalize()}...")


if __name__ == "__main__":
    main()
