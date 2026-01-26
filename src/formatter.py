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
from pathlib import Path

import click

from .extraction_pipeline import ExtractionPipeline

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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
    default="gpt-4",
    help="LLM model to use (default: gpt-4)",
)
@click.option(
    "--no-tables",
    is_flag=True,
    help="Don't extract tables from PDF",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed processing logs",
)
def main(input: Path, output: Path, llm_model: str, no_tables: bool, verbose: bool):
    """
    Extract Universal Carrier Format schema from carrier API documentation PDF.

    INPUT: Path to PDF file containing carrier API documentation

    Example:
        python -m src.formatter examples/dhl_express_api_docs.pdf --output output/dhl_schema.json
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

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
        pipeline = ExtractionPipeline(
            llm_model=llm_model, extract_tables=not no_tables
        )

        # Process PDF
        click.echo(f"📄 Processing: {input}")
        click.echo(f"💾 Output: {output}")
        click.echo()

        schema = pipeline.process(str(input), str(output))

        click.echo()
        click.echo("=" * 70)
        click.echo("✅ Extraction Complete!")
        click.echo("=" * 70)
        click.echo(f"Carrier: {schema.name}")
        click.echo(f"Base URL: {schema.base_url}")
        click.echo(f"Endpoints: {len(schema.endpoints)}")
        click.echo(f"Output: {output}")
        click.echo()

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
