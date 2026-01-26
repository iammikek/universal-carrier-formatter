"""
Extraction Pipeline

Laravel Equivalent: app/Services/ExtractionPipelineService.php

Orchestrates the complete extraction process:
PDF → Parser → LLM → Validator → Universal Carrier Format JSON

In Laravel, you'd have:
class ExtractionPipelineService
{
    public function __construct(
        private PdfParserService $parser,
        private LlmExtractorService $extractor,
        private CarrierValidator $validator
    ) {}

    public function process(string $pdfPath): CarrierSchema
    {
        $text = $this->parser->extract($pdfPath);
        $schema = $this->extractor->extract($text);
        return $this->validator->validate($schema);
    }
}
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .core.schema import UniversalCarrierFormat
from .core.validator import CarrierValidator

from .llm_extractor import LlmExtractorService
from .pdf_parser import PdfParserService

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    """
    Complete extraction pipeline: PDF → Universal Carrier Format.

    Laravel Equivalent: app/Services/ExtractionPipelineService.php

    This orchestrates:
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
        llm_model: str = "gpt-4",
        extract_tables: bool = True,
        llm_api_key: Optional[str] = None,
    ):
        """
        Initialize extraction pipeline.

        Args:
            llm_model: LLM model to use (default: "gpt-4")
            extract_tables: Whether to extract tables from PDF (default: True)
            llm_api_key: LLM API key (default: from environment)
        """
        self.pdf_parser = PdfParserService(config={"extract_tables": extract_tables})
        self.llm_extractor = LlmExtractorService(
            model=llm_model, api_key=llm_api_key
        )
        self.validator = CarrierValidator()

    def process(
        self, pdf_path: str, output_path: Optional[str] = None
    ) -> UniversalCarrierFormat:
        """
        Process PDF and extract Universal Carrier Format schema.

        Laravel Equivalent:
        public function process(string $pdfPath, ?string $outputPath = null): CarrierSchema

        Args:
            pdf_path: Path to PDF file
            output_path: Optional path to save output JSON

        Returns:
            UniversalCarrierFormat: Extracted and validated schema
        """
        logger.info(f"Starting extraction pipeline for: {pdf_path}")

        # Step 1: Extract text from PDF
        logger.info("Step 1: Extracting text from PDF...")
        pdf_text = self.pdf_parser.extract_text(pdf_path)
        metadata = self.pdf_parser.extract_metadata(pdf_path)
        logger.info(
            f"Extracted {len(pdf_text):,} characters from {metadata.get('page_count')} pages"
        )

        # Step 2: Extract schema using LLM
        logger.info("Step 2: Extracting schema using LLM...")
        schema = self.llm_extractor.extract_schema(pdf_text)

        # Step 3: Extract additional information
        logger.info("Step 3: Extracting field mappings and constraints...")
        field_mappings = self.llm_extractor.extract_field_mappings(
            pdf_text, schema.name
        )
        constraints = self.llm_extractor.extract_constraints(pdf_text)

        # Step 4: Save output if path specified
        if output_path:
            logger.info(f"Step 4: Saving to {output_path}...")
            self._save_output(schema, field_mappings, constraints, output_path)

        logger.info(
            f"✅ Extraction complete: {schema.name} with {len(schema.endpoints)} endpoints"
        )

        return schema

    def _save_output(
        self,
        schema: UniversalCarrierFormat,
        field_mappings: list,
        constraints: list,
        output_path: str,
    ) -> None:
        """
        Save extracted schema and additional data to JSON file.

        Args:
            schema: Extracted Universal Carrier Format schema
            field_mappings: Field name mappings
            constraints: Business rules and constraints
            output_path: Path to save JSON file
        """
        output_data = {
            "schema": schema.dict(),
            "field_mappings": field_mappings,
            "constraints": constraints,
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)

        logger.info(f"Saved output to: {output_path}")
