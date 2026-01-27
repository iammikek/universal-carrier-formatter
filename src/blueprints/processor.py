"""
Blueprint Processor - Orchestrate blueprint loading, validation, and conversion.

Laravel Equivalent: app/Services/Blueprints/BlueprintProcessor.php

Main entry point for processing blueprints. Orchestrates:
1. Loading blueprint YAML file
2. Validating blueprint structure
3. Converting to Universal Carrier Format
"""

import logging
from pathlib import Path
from typing import Any

from .converter import BlueprintConverter
from .loader import BlueprintLoader
from .validator import BlueprintValidator

logger = logging.getLogger(__name__)


class BlueprintProcessor:
    """
    Process blueprints end-to-end: load → validate → convert.

    Laravel Equivalent:
    class BlueprintProcessor
    {
        public function process(string $filepath): UniversalCarrierFormat
        {
            $loader = new BlueprintLoader();
            $validator = new BlueprintValidator();
            $converter = new BlueprintConverter();

            $blueprint = $loader->load($filepath);
            $errors = $validator->validate($blueprint);
            if (!empty($errors)) {
                throw new ValidationException($errors);
            }
            return $converter->convert($blueprint);
        }
    }
    """

    def __init__(self):
        """Initialize processor with loader, validator, and converter."""
        self.loader = BlueprintLoader()
        self.validator = BlueprintValidator()
        self.converter = BlueprintConverter()

    def process(self, filepath: str | Path) -> Any:
        """
        Process a blueprint file: load → validate → convert.

        Args:
            filepath: Path to blueprint YAML file

        Returns:
            UniversalCarrierFormat instance

        Raises:
            FileNotFoundError: If blueprint file doesn't exist
            ValueError: If blueprint is invalid or conversion fails
        """
        logger.info(f"Processing blueprint: {filepath}")

        # Step 1: Load blueprint
        try:
            blueprint = self.loader.load(filepath)
        except FileNotFoundError:
            logger.error(f"Blueprint file not found: {filepath}")
            raise
        except ValueError as err:
            logger.error(f"Failed to load blueprint: {err}")
            raise ValueError(f"Failed to load blueprint: {err}") from err

        # Step 2: Validate blueprint
        errors = self.validator.validate(blueprint)
        if errors:
            error_msg = "Blueprint validation failed:\n" + "\n".join(
                f"  - {error}" for error in errors
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug("Blueprint validation passed")

        # Step 3: Convert to Universal Carrier Format
        try:
            universal_format = self.converter.convert(blueprint)
            logger.info(
                f"Successfully converted blueprint to Universal Carrier Format: {universal_format.name}"
            )
            return universal_format
        except ValueError as e:
            logger.error(f"Failed to convert blueprint: {e}")
            raise ValueError(f"Failed to convert blueprint: {e}") from e

    def process_from_string(self, yaml_content: str) -> Any:
        """
        Process blueprint from YAML string content.

        Args:
            yaml_content: YAML string content

        Returns:
            UniversalCarrierFormat instance

        Raises:
            ValueError: If blueprint is invalid or conversion fails
        """
        logger.info("Processing blueprint from string content")

        # Step 1: Load blueprint
        try:
            blueprint = self.loader.load_from_string(yaml_content)
        except ValueError as e:
            logger.error(f"Failed to load blueprint from string: {e}")
            raise ValueError(f"Failed to load blueprint: {e}") from e

        # Step 2: Validate blueprint
        errors = self.validator.validate(blueprint)
        if errors:
            error_msg = "Blueprint validation failed:\n" + "\n".join(
                f"  - {error}" for error in errors
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug("Blueprint validation passed")

        # Step 3: Convert to Universal Carrier Format
        try:
            universal_format = self.converter.convert(blueprint)
            logger.info(
                f"Successfully converted blueprint to Universal Carrier Format: {universal_format.name}"
            )
            return universal_format
        except ValueError as e:
            logger.error(f"Failed to convert blueprint: {e}")
            raise ValueError(f"Failed to convert blueprint: {e}") from e
