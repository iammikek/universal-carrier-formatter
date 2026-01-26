"""
Mapper Generator CLI - Command-line interface for generating mappers.

Laravel Equivalent: app/Console/Commands/GenerateMapper.php

CLI command to generate mapper code from Universal Carrier Format schemas
(extracted from PDFs or loaded from blueprints).
"""

import logging
import sys
from pathlib import Path

import click

from .core.schema import UniversalCarrierFormat
from .mapper_generator import MapperGeneratorService

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
    help="Output mapper file path (default: src/mappers/{carrier_name}_mapper.py)",
)
@click.option(
    "--llm-model",
    type=str,
    default="gpt-4.1-mini",
    help="LLM model to use for code generation (default: gpt-4.1-mini)",
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
):
    """
    Generate mapper code from Universal Carrier Format schema.

    INPUT: Path to Universal Carrier Format JSON file (from PDF extraction or blueprint)

    Example:
        python -m src.mapper_generator_cli output/dhl_schema.json --output src/mappers/dhl_express_mapper.py
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Load schema from JSON
        click.echo(f"Loading schema from: {input}")
        schema = UniversalCarrierFormat.from_json_file(str(input))

        # Determine output path
        if output is None:
            carrier_name_safe = schema.name.lower().replace(" ", "_").replace("-", "_")
            output = Path("src/mappers") / f"{carrier_name_safe}_mapper.py"
            output.parent.mkdir(exist_ok=True)

        # Generate mapper
        click.echo(f"Generating mapper for: {schema.name}")
        click.echo(f"Using LLM model: {llm_model}")

        generator = MapperGeneratorService(model=llm_model)
        mapper_code = generator.generate_mapper(schema, output_path=output)

        click.echo(f"✅ Successfully generated mapper: {output}")
        click.echo(f"   Carrier: {schema.name}")
        click.echo(f"   Endpoints: {len(schema.endpoints)}")
        click.echo(f"   File size: {len(mapper_code)} characters")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: Schema file not found: {e}", err=True)
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
