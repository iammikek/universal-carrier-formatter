"""
PDF Parser Service

Laravel Equivalent: app/Services/PdfParserService.php

This service handles extraction of text content from PDF files,
specifically designed for parsing carrier API documentation.

In Laravel, you'd have:
class PdfParserService
{
    public function __construct(
        private Config $config
    ) {}

    public function extractText(string $pdfPath): string
    {
        if (!file_exists($pdfPath)) {
            throw new FileNotFoundException("PDF not found: {$pdfPath}");
        }

        // Extract text using PDF library
        $text = $this->parsePdf($pdfPath);

        Log::info("Extracted text from PDF", [
            'path' => $pdfPath,
            'length' => strlen($text)
        ]);

        return $text;
    }
}
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import pdfplumber

logger = logging.getLogger(__name__)


class PdfParserService:
    """
    PDF parsing service for extracting text from carrier API documentation.

    Laravel Equivalent: app/Services/PdfParserService.php

    This service handles:
    - Text extraction from PDF files
    - Multi-page PDF processing
    - Error handling for invalid/missing files
    - Metadata extraction

    Usage:
        parser = PdfParserService()
        text = parser.extract_text('path/to/file.pdf')
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PDF parser service.

        Laravel Equivalent:
        public function __construct(
            private Config $config
        ) {}

        Args:
            config: Optional configuration dictionary
                - 'extract_tables': bool - Whether to extract table data (default: False)
                - 'combine_pages': bool - Combine all pages into single text (default: True)
        """
        self.config = config or {}
        self.extract_tables = self.config.get("extract_tables", False)
        self.combine_pages = self.config.get("combine_pages", True)

    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text content from PDF file.

        Laravel Equivalent:
        public function extractText(string $pdfPath): string
        {
            if (!file_exists($pdfPath)) {
                throw new FileNotFoundException("PDF not found: {$pdfPath}");
            }

            $text = $this->parsePdf($pdfPath);
            Log::info("Extracted text from PDF", ['path' => $pdfPath]);

            return $text;
        }

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text content as string

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF is invalid or corrupted
            PermissionError: If file cannot be read
        """
        # Validate file exists
        self._validate_pdf_path(pdf_path)

        logger.info(f"Starting PDF text extraction: {pdf_path}")

        try:
            # Extract text using pdfplumber
            text = self._extract_text_from_pdf(pdf_path)

            logger.info(
                f"Successfully extracted text from PDF: {pdf_path}",
                extra={
                    "text_length": len(text),
                    "pages": self._get_page_count(pdf_path),
                },
            )

            return text

        except Exception:
            logger.error(f"Failed to extract text from PDF: {pdf_path}", exc_info=True)
            raise

    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF file.

        Laravel Equivalent:
        public function extractMetadata(string $pdfPath): array
        {
            // Extract PDF metadata
        }

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary containing PDF metadata:
            - page_count: Number of pages
            - title: PDF title (if available)
            - author: PDF author (if available)
            - created: Creation date (if available)
        """
        self._validate_pdf_path(pdf_path)

        try:
            path = Path(pdf_path)
            file_size = path.stat().st_size if path.exists() else 0

            with pdfplumber.open(pdf_path) as pdf:
                metadata = {
                    "page_count": len(pdf.pages),
                    "file_size": file_size,
                    "title": pdf.metadata.get("Title", ""),
                    "author": pdf.metadata.get("Author", ""),
                    "created": pdf.metadata.get("CreationDate", ""),
                }

                logger.debug(f"Extracted metadata from PDF: {pdf_path}", extra=metadata)
                return metadata

        except Exception as e:
            logger.error(
                f"Failed to extract metadata from PDF: {pdf_path}", exc_info=True
            )
            raise ValueError(f"Could not extract metadata from PDF: {e}") from e

    def _validate_pdf_path(self, pdf_path: str) -> None:
        """
        Validate that PDF file exists and is readable.

        Laravel Equivalent:
        private function validatePdfPath(string $path): void
        {
            if (!file_exists($path)) {
                throw new FileNotFoundException("PDF not found: {$path}");
            }

            if (!is_readable($path)) {
                throw new PermissionException("Cannot read PDF: {$path}");
            }
        }

        Args:
            pdf_path: Path to PDF file

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file cannot be read
            ValueError: If path is not a file
        """
        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {pdf_path}")

        if not path.stat().st_size > 0:
            raise ValueError(f"PDF file is empty: {pdf_path}")

        # Check if readable (like is_readable() in PHP)
        if not path.stat().st_mode & 0o444:  # Check read permission
            raise PermissionError(f"Cannot read PDF file: {pdf_path}")

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Internal method to extract text from PDF using pdfplumber.

        Laravel Equivalent:
        private function parsePdf(string $path): string
        {
            // PDF parsing implementation
        }

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text content
        """
        text_parts = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract text from page
                    page_text = page.extract_text()

                    if page_text:
                        if self.combine_pages:
                            text_parts.append(page_text)
                        else:
                            # Add page separator if not combining
                            text_parts.append(f"\n--- Page {page_num} ---\n{page_text}")

                    # Extract tables if configured (like extracting structured data)
                    if self.extract_tables:
                        tables = page.extract_tables()
                        if tables:
                            for table_idx, table in enumerate(tables, start=1):
                                # Convert table to Markdown format
                                table_text = self._table_to_text(table)
                                # Mark table clearly for LLM processing
                                text_parts.append(
                                    f"\n<!-- TABLE START: Page {page_num}, Table {table_idx} -->\n"
                                    f"{table_text}\n"
                                    f"<!-- TABLE END -->\n"
                                )

            # Combine all text parts
            combined_text = "\n".join(text_parts)

            if not combined_text.strip():
                logger.warning(f"No text content found in PDF: {pdf_path}")
                raise ValueError(
                    f"PDF appears to be empty or contains only images: {pdf_path}"
                )

            return combined_text

        except Exception as e:
            # Check if it's a PDF syntax error (pdfplumber may raise various exceptions)
            error_msg = str(e).lower()
            if (
                "syntax" in error_msg
                or "invalid" in error_msg
                or "corrupted" in error_msg
            ):
                raise ValueError(f"Invalid or corrupted PDF file: {pdf_path}") from e
            logger.error(f"Error extracting text from PDF: {pdf_path}", exc_info=True)
            raise ValueError(f"Failed to extract text from PDF: {e}") from e

    def _table_to_text(self, table: list) -> str:
        """
        Convert table data to Markdown table format for better LLM parsing.

        Laravel Equivalent:
        private function tableToText(array $table): string
        {
            // Convert table array to readable text
        }

        Args:
            table: Table data as list of lists (first row is typically headers)

        Returns:
            Markdown-formatted table string
        """
        if not table:
            return ""

        if len(table) == 0:
            return ""

        # Assume first row is headers
        headers = table[0] if table else []
        rows = table[1:] if len(table) > 1 else []

        # Convert headers to strings
        header_row = [str(cell) if cell is not None else "" for cell in headers]

        # Create Markdown table
        lines = []

        # Header row
        lines.append("| " + " | ".join(header_row) + " |")

        # Separator row
        lines.append("| " + " | ".join(["---"] * len(header_row)) + " |")

        # Data rows
        for row in rows:
            row_text = [str(cell) if cell is not None else "" for cell in row]
            # Pad row if shorter than headers
            while len(row_text) < len(header_row):
                row_text.append("")
            lines.append("| " + " | ".join(row_text) + " |")

        return "\n".join(lines)

    def _get_page_count(self, pdf_path: str) -> int:
        """
        Get number of pages in PDF.

        Laravel Equivalent:
        private function getPageCount(string $path): int
        {
            // Get PDF page count
        }

        Args:
            pdf_path: Path to PDF file

        Returns:
            Number of pages
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except Exception:
            return 0
