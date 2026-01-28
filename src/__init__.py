"""
Universal Carrier Formatter - Main package.

- Module files provide services (formatter, extraction, mappers, etc.)
- Core schema and validation live in core/
- Main entry point is formatter.py
"""

__version__ = "0.1.0"

# Export main classes for easy importing
from .extraction_pipeline import ExtractionPipeline
from .llm_extractor import LlmExtractorService
from .pdf_parser import PdfParserService

__all__ = ["PdfParserService", "LlmExtractorService", "ExtractionPipeline"]
