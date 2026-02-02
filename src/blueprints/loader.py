"""
Blueprint Loader - Load and parse YAML blueprint files.

Loads YAML files from the blueprints/ directory and parses them into
Python dictionaries for further processing.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)


class BlueprintLoader:
    """
    Loads and parses YAML blueprint files.
    """

    def load(self, filepath: str | Path) -> Dict[str, Any]:
        """
        Load a blueprint YAML file and return parsed data.

        Args:
            filepath: Path to blueprint YAML file (relative or absolute)

        Returns:
            Dictionary containing parsed YAML data

        Raises:
            FileNotFoundError: If blueprint file doesn't exist
            yaml.YAMLError: If YAML is invalid
            ValueError: If file is empty or invalid
        """
        filepath = Path(filepath)

        # Handle relative paths - assume blueprints/ directory
        if not filepath.is_absolute():
            # Try blueprints/ directory first
            blueprint_path = Path("blueprints") / filepath
            if not blueprint_path.exists():
                # Try as absolute path from project root
                blueprint_path = filepath
            filepath = blueprint_path

        if not filepath.exists():
            raise FileNotFoundError(f"Blueprint file not found: {filepath}")

        logger.info(f"Loading blueprint from: {filepath}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:
                raise ValueError(f"Blueprint file is empty: {filepath}")

            if not isinstance(data, dict):
                raise ValueError(
                    f"Blueprint file must contain a YAML dictionary, got: {type(data)}"
                )

            logger.debug(f"Successfully loaded blueprint: {filepath}")
            return data

        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in blueprint file {filepath}: {e}")
            raise ValueError(f"Invalid YAML in blueprint file: {e}") from e

    def load_from_string(self, yaml_content: str) -> Dict[str, Any]:
        """
        Load blueprint from YAML string content.

        Args:
            yaml_content: YAML string content

        Returns:
            Dictionary containing parsed YAML data

        Raises:
            yaml.YAMLError: If YAML is invalid
            ValueError: If content is empty or invalid
        """
        if not yaml_content or not yaml_content.strip():
            raise ValueError("YAML content is empty")

        try:
            data = yaml.safe_load(yaml_content)

            if data is None:
                raise ValueError("YAML content is empty")

            if not isinstance(data, dict):
                raise ValueError(
                    f"YAML content must be a dictionary, got: {type(data)}"
                )

            return data

        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML content: {e}")
            raise ValueError(f"Invalid YAML content: {e}") from e
