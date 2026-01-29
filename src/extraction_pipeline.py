"""
Extraction Pipeline.

Orchestrates the complete extraction process:
PDF → Parser → LLM → Validator → Universal Carrier Format JSON.
"""

import json
import logging
import os
from pathlib import Path
from typing import Callable, Optional

from .constraint_code_generator import generate_validators_file
from .core.config import (
    DEFAULT_LLM_PROVIDER,
    KEY_CONSTRAINTS,
    KEY_EDGE_CASES,
    KEY_EXTRACTION_METADATA,
    KEY_FIELD_MAPPINGS,
    KEY_GENERATOR_VERSION,
    KEY_SCHEMA,
    KEY_SCHEMA_VERSION,
    LLM_PROVIDER_ENV,
    STEP_EXTRACT,
    STEP_PARSE,
    STEP_SAVE,
    STEP_VALIDATE,
)
from .core.contract import SCHEMA_VERSION, get_generator_version
from .core.schema import UniversalCarrierFormat
from .core.validator import CarrierValidator
from .llm_extractor import LlmExtractorService
from .pdf_parser import PdfParserService
from .prompts import get_prompt_versions

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    """
    Complete extraction pipeline: PDF → Universal Carrier Format.

    Orchestrates:
    1. PDF parsing (extract text)
    2. LLM extraction (extract schema)
    3. Validation (ensure schema is valid)
    4. Output generation (save to file)

    Usage:
        pipeline = ExtractionPipeline()
        schema = pipeline.process('examples/dhl_express_api_docs.pdf')
    """

    def __init__(
        self,
        llm_model: Optional[str] = None,
        extract_tables: bool = True,
        llm_api_key: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """
        Initialize extraction pipeline.

        Args:
            llm_model: LLM model name (default: provider-specific)
            extract_tables: Whether to extract tables from PDF (default: True)
            llm_api_key: API key (default: from OPENAI_API_KEY or ANTHROPIC_API_KEY per provider)
            provider: "openai" or "anthropic" (default: from LLM_PROVIDER env or "openai")
        """
        provider = (
            (provider or os.getenv(LLM_PROVIDER_ENV) or DEFAULT_LLM_PROVIDER)
            .strip()
            .lower()
        )
        self.pdf_parser = PdfParserService(config={"extract_tables": extract_tables})
        self.llm_extractor = LlmExtractorService(
            model=llm_model, api_key=llm_api_key, provider=provider
        )
        self.validator = CarrierValidator()

    def process(
        self,
        pdf_path: str,
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable[[str, str], None]] = None,
        generate_validators: bool = True,
        dump_pdf_text_path: Optional[str] = None,
        extracted_text_path: Optional[str] = None,
    ) -> UniversalCarrierFormat:
        """
        Process PDF and extract Universal Carrier Format schema.

        Args:
            pdf_path: Path to PDF file (used for output naming when extracted_text_path set)
            output_path: Optional path to save output JSON
            progress_callback: Optional callback function(step, message) for progress updates
            generate_validators: If True and constraints exist, write Pydantic validators
                to a _validators.py file next to the JSON output (Scenario 2).
            dump_pdf_text_path: If set, write the extracted PDF text (exact string sent to
                the LLM) to this file for inspection.
            extracted_text_path: If set, skip PDF parsing and use this file's contents as
                the text sent to the LLM. Saves re-extracting from PDF on each run.

        Returns:
            UniversalCarrierFormat: Extracted and validated schema
        """
        logger.info(f"Starting extraction pipeline for: {pdf_path}")

        # Step 1: Get text (from file or by extracting from PDF)
        if extracted_text_path:
            if progress_callback:
                progress_callback(
                    STEP_PARSE, f"Loading extracted text from {extracted_text_path}..."
                )
            else:
                logger.info(
                    f"Step 1: Loading extracted text from {extracted_text_path}..."
                )
            pdf_text = Path(extracted_text_path).read_text(encoding="utf-8")
            char_count = len(pdf_text)
            page_count = 0
            if progress_callback:
                progress_callback(
                    STEP_PARSE, f"Loaded {char_count:,} characters (skipped PDF)"
                )
            else:
                logger.info(
                    f"Loaded {char_count:,} characters from file (PDF step skipped)"
                )
        else:
            if progress_callback:
                progress_callback(STEP_PARSE, "Reading PDF file...")
            else:
                logger.info("Step 1: Extracting text from PDF...")

            pdf_text = self.pdf_parser.extract_text(pdf_path)
            metadata = self.pdf_parser.extract_metadata(pdf_path)
            page_count = metadata.get("page_count", 0)
            char_count = len(pdf_text)

            if dump_pdf_text_path:
                dump_file = Path(dump_pdf_text_path)
                dump_file.parent.mkdir(parents=True, exist_ok=True)
                dump_file.write_text(pdf_text, encoding="utf-8")
                logger.info(
                    f"Dumped extracted PDF text to {dump_pdf_text_path} ({char_count:,} chars)"
                )
                if progress_callback:
                    progress_callback(
                        STEP_PARSE, f"Dumped text to {dump_pdf_text_path}"
                    )

            if progress_callback:
                progress_callback(
                    STEP_PARSE,
                    f"Extracted {char_count:,} characters from {page_count} page(s)",
                )
            else:
                logger.info(
                    f"Extracted {char_count:,} characters from {page_count} pages"
                )

        # Step 2: Extract schema using LLM
        if progress_callback:
            progress_callback(
                STEP_EXTRACT, "Sending to LLM (this may take a minute)..."
            )
        else:
            logger.info("Step 2: Extracting schema using LLM...")

        schema = self.llm_extractor.extract_schema(pdf_text)

        if progress_callback:
            progress_callback(
                STEP_EXTRACT,
                f"Extracted schema: {schema.name} with {len(schema.endpoints)} endpoint(s)",
            )

        # Step 3: Extract additional information
        if progress_callback:
            progress_callback(
                STEP_VALIDATE, "Extracting field mappings, constraints, edge cases..."
            )
        else:
            logger.info(
                "Step 3: Extracting field mappings, constraints, and edge cases..."
            )

        field_mappings = self.llm_extractor.extract_field_mappings(
            pdf_text, schema.name
        )
        constraints = self.llm_extractor.extract_constraints(pdf_text)
        edge_cases = self.llm_extractor.extract_edge_cases(pdf_text)

        if progress_callback:
            progress_callback(
                STEP_VALIDATE,
                f"Found {len(field_mappings)} mapping(s), {len(constraints)} constraint(s), {len(edge_cases)} edge case(s)",
            )

        # Step 4: Save output if path specified
        if output_path:
            if progress_callback:
                progress_callback(STEP_SAVE, f"Saving to {output_path}...")
            else:
                logger.info(f"Step 4: Saving to {output_path}...")

            extraction_metadata = {
                "llm_config": self.llm_extractor.get_config(),
                "prompt_versions": get_prompt_versions(),
            }
            self._save_output(
                schema,
                field_mappings,
                constraints,
                edge_cases,
                output_path,
                generate_validators,
                extraction_metadata=extraction_metadata,
            )

            if progress_callback:
                progress_callback(STEP_SAVE, "Saved successfully!")

        logger.info(
            f"✅ Extraction complete: {schema.name} with {len(schema.endpoints)} endpoints"
        )

        return schema

    def _save_output(
        self,
        schema: UniversalCarrierFormat,
        field_mappings: list,
        constraints: list,
        edge_cases: list,
        output_path: str,
        generate_validators: bool = True,
        extraction_metadata: Optional[dict] = None,
    ) -> None:
        """
        Save extracted schema and additional data to JSON file.

        All LLM-extracted data is preserved: no deduplication or trimming of
        schema, field_mappings, constraints, or edge_cases.

        Args:
            schema: Extracted Universal Carrier Format schema
            field_mappings: Field name mappings
            constraints: Business rules and constraints
            edge_cases: Route-specific edge cases (Scenario 3)
            output_path: Path to save JSON file
            generate_validators: If True and constraints exist, also write validators .py
            extraction_metadata: Optional dict with llm_config, prompt_versions (for reproducibility)
        """
        output_data = {
            KEY_SCHEMA_VERSION: SCHEMA_VERSION,
            KEY_GENERATOR_VERSION: get_generator_version(),
            KEY_SCHEMA: schema.model_dump(),
            KEY_FIELD_MAPPINGS: field_mappings,
            KEY_CONSTRAINTS: constraints,
            KEY_EDGE_CASES: edge_cases,
        }
        if extraction_metadata:
            output_data[KEY_EXTRACTION_METADATA] = extraction_metadata

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)

        logger.info(f"Saved output to: {output_path}")

        if generate_validators and constraints:
            validators_path = output_file.with_name(output_file.stem + "_validators.py")
            generate_validators_file(constraints, str(validators_path))
