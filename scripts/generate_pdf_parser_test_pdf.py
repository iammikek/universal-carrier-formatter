#!/usr/bin/env python3
"""
Generate a small PDF for tests/integration/test_pdf_parser.py.

The PDF is one page, contains API-related keywords so
test_extract_text_contains_api_keywords passes, and stays small for fast test runs.

Run from repo root: python scripts/generate_pdf_parser_test_pdf.py
Output: examples/pdf_parser_test.pdf
"""

from pathlib import Path


def main() -> None:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise SystemExit("PyMuPDF is required: pip install pymupdf")

    examples = Path("examples")
    examples.mkdir(exist_ok=True)
    out = examples / "pdf_parser_test.pdf"

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    # Text that pdfplumber can extract; includes api, endpoint, request, response, http, method
    body = (
        "API Documentation Sample\n\n"
        "This is a small test PDF for the PDF parser integration tests. "
        "It contains API-related keywords: endpoint, request, response, HTTP method."
    )
    page.insert_text((72, 72), body, fontsize=12)
    doc.save(str(out))
    doc.close()

    size = out.stat().st_size
    print(f"Wrote {out} ({size} bytes)")


if __name__ == "__main__":
    main()
