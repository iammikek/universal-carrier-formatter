"""
Blueprint CLI - Command-line interface for processing blueprints.

Laravel Equivalent: app/Console/Commands/ProcessBlueprint.php

CLI command to process blueprint YAML files and convert them to
Universal Carrier Format JSON.
"""

import logging
import sys
from pathlib import Path

import click

from .processor import BlueprintProcessor

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

    try:
        processor = BlueprintProcessor()

        if validate_only:
            # Just validate, don't convert
            from .loader import BlueprintLoader
            from .validator import BlueprintValidator

            loader = BlueprintLoader()
            validator = BlueprintValidator()

            blueprint = loader.load(input)
            errors = validator.validate(blueprint)

            if errors:
                click.echo("❌ Blueprint validation failed:", err=True)
                for error in errors:
                    click.echo(f"  - {error}", err=True)
                sys.exit(1)
            else:
                click.echo("✅ Blueprint is valid!")
                sys.exit(0)

        # Process blueprint
        click.echo(f"Processing blueprint: {input}")
        universal_format = processor.process(input)

        # Determine output path
        if output is None:
            carrier_name = universal_format.name.lower().replace(" ", "_")
            output = Path("output") / f"{carrier_name}_schema.json"
            output.parent.mkdir(exist_ok=True)

        # Save to JSON
        universal_format.to_json_file(str(output))
        click.echo(f"✅ Successfully converted blueprint to: {output}")
        click.echo(f"   Carrier: {universal_format.name}")
        click.echo(f"   Base URL: {universal_format.base_url}")
        click.echo(f"   Endpoints: {len(universal_format.endpoints)}")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
