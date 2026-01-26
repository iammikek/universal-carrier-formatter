"""
Blueprint CLI - Command-line interface for processing blueprints.

Laravel Equivalent: app/Console/Commands/ProcessBlueprint.php

CLI command to process blueprint YAML files and convert them to
Universal Carrier Format JSON.
"""

import logging
import sys
import time
from pathlib import Path

import click

from .processor import BlueprintProcessor

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
    "--validate-only",
    is_flag=True,
    help="Only validate blueprint, don't convert",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(input: Path, output: Path | None, validate_only: bool, verbose: bool):
    """
    Process a blueprint YAML file and convert to Universal Carrier Format.

    INPUT: Path to blueprint YAML file (e.g., blueprints/dhl_express.yaml)

    Example:
        python -m src.blueprints.cli blueprints/dhl_express.yaml --output output/dhl_schema.json
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
    click.echo("Blueprint Processor")
    click.echo("=" * 70)
    click.echo()

    try:
        processor = BlueprintProcessor()

        if validate_only:
            # Just validate, don't convert
            click.echo("🔍 Validating blueprint...")
            click.echo(f"   Input: {input}")
            click.echo()

            from .loader import BlueprintLoader
            from .validator import BlueprintValidator

            loader = BlueprintLoader()
            validator = BlueprintValidator()

            blueprint = loader.load(input)
            errors = validator.validate(blueprint)

            if errors:
                click.echo()
                click.echo("=" * 70, err=True)
                click.echo("❌ Blueprint validation failed", err=True)
                click.echo("=" * 70, err=True)
                for error in errors:
                    click.echo(f"   - {error}", err=True)
                click.echo()
                sys.exit(1)
            else:
                click.echo()
                click.echo("=" * 70)
                click.echo("✅ Blueprint is valid!")
                click.echo("=" * 70)
                click.echo()
                sys.exit(0)

        # Process blueprint
        click.echo("📄 Processing blueprint...")
        click.echo(f"   Input: {input}")
        click.echo()

        click.echo("   ⏳ Loading and validating...")
        universal_format = processor.process(input)

        # Determine output path
        if output is None:
            carrier_name = universal_format.name.lower().replace(" ", "_")
            output = Path("output") / f"{carrier_name}_schema.json"
            output.parent.mkdir(exist_ok=True)

        click.echo("   💾 Saving to JSON...")
        universal_format.to_json_file(str(output))

        elapsed = time.time() - start_time

        click.echo()
        click.echo("=" * 70)
        click.echo("✅ Blueprint Processed Successfully!")
        click.echo("=" * 70)
        click.echo(f"📦 Carrier: {universal_format.name}")
        click.echo(f"🌐 Base URL: {universal_format.base_url}")
        click.echo(f"🔗 Endpoints: {len(universal_format.endpoints)}")
        if universal_format.authentication:
            click.echo(f"🔐 Authentication: {len(universal_format.authentication)} method(s)")
        click.echo(f"💾 Output: {output}")
        click.echo(f"⏱️  Time: {elapsed:.1f}s")
        click.echo()

    except KeyboardInterrupt:
        click.echo()
        click.echo("❌ Interrupted by user", err=True)
        sys.exit(1)
    except FileNotFoundError as e:
        click.echo()
        click.echo("=" * 70, err=True)
        click.echo("❌ Error: Blueprint file not found", err=True)
        click.echo("=" * 70, err=True)
        click.echo(f"   {e}", err=True)
        click.echo()
        sys.exit(1)
    except ValueError as e:
        click.echo()
        click.echo("=" * 70, err=True)
        click.echo("❌ Error", err=True)
        click.echo("=" * 70, err=True)
        click.echo(f"   {e}", err=True)
        click.echo()
        if verbose:
            import traceback

            traceback.print_exc()
        else:
            click.echo("   Run with --verbose for more details", err=True)
        click.echo()
        sys.exit(1)
    except Exception as e:
        click.echo()
        click.echo("=" * 70, err=True)
        click.echo("❌ Unexpected error", err=True)
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


if __name__ == "__main__":
    main()
