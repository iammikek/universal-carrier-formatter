"""
Mapper Generator CLI - Command-line interface for generating mappers.

Generates mapper code from Universal Carrier Format schemas
(extracted from PDFs or loaded from blueprints).
"""

import json
import logging
import sys
import time
from pathlib import Path

import click

from .core.config import DEFAULT_LLM_MODEL, KEY_SCHEMA
from .core.contract import check_schema_version_and_warn
from .core.schema import UniversalCarrierFormat
from .mapper_generator import MapperGeneratorService

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
    help="Output mapper file path (default: src/mappers/{carrier_name}_mapper.py)",
)
@click.option(
    "--llm-model",
    type=str,
    default=DEFAULT_LLM_MODEL,
    help=f"LLM model to use for code generation (default: {DEFAULT_LLM_MODEL})",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(
    input: Path,
    output: Path | None,
    llm_model: str,
    verbose: bool,
) -> None:
    """
    Generate mapper code from Universal Carrier Format schema.

    INPUT: Path to Universal Carrier Format JSON file (from PDF extraction or blueprint)

    Example:
        python -m src.mapper_generator_cli output/dhl_schema.json --output src/mappers/dhl_express_mapper.py
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        # Show all logs in verbose mode
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            force=True,
        )

    try:
        start_time = time.time()

        click.echo("=" * 70)
        click.echo("Mapper Generator")
        click.echo("=" * 70)
        click.echo()

        # Load schema from JSON
        click.echo("📂 Loading schema...")
        click.echo(f"   Input: {input}")
        data = json.loads(input.read_text(encoding="utf-8"))
        check_schema_version_and_warn(data, source=str(input))
        schema_data = data.get(KEY_SCHEMA, data)
        schema = UniversalCarrierFormat.model_validate(schema_data)
        click.echo(f"   ✅ Loaded: {schema.name}")
        click.echo()

        # Determine output path
        if output is None:
            carrier_name_safe = schema.name.lower().replace(" ", "_").replace("-", "_")
            output = Path("src/mappers") / f"{carrier_name_safe}_mapper.py"
            output.parent.mkdir(exist_ok=True)

        # Generate mapper
        click.echo("🤖 Generating mapper code...")
        click.echo(f"   Carrier: {schema.name}")
        click.echo(f"   Model: {llm_model}")
        click.echo(f"   Endpoints: {len(schema.endpoints)}")
        click.echo()
        click.echo("   ⏳ Sending to LLM (this may take 30-60 seconds)...")

        generator = MapperGeneratorService(model=llm_model)
        mapper_code = generator.generate_mapper(schema, output_path=output)

        elapsed = time.time() - start_time

        click.echo()
        click.echo("=" * 70)
        click.echo("✅ Mapper Generated Successfully!")
        click.echo("=" * 70)
        click.echo(f"📦 Carrier: {schema.name}")
        click.echo(f"📄 Output: {output}")
        click.echo(f"📊 Endpoints: {len(schema.endpoints)}")
        click.echo(f"📝 Code size: {len(mapper_code):,} characters")
        click.echo(f"⏱️  Time: {elapsed:.1f}s")
        click.echo()

    except KeyboardInterrupt:
        click.echo()
        click.echo("❌ Interrupted by user", err=True)
        sys.exit(1)
    except FileNotFoundError as e:
        click.echo()
        click.echo("=" * 70, err=True)
        click.echo("❌ Error: Schema file not found", err=True)
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
    except (ValueError, OSError) as e:
        click.echo(f"Error: {e}", err=True)
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
