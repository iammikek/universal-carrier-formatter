#!/usr/bin/env python3
"""
Test PDF Parser on DHL Express API Documentation

This script demonstrates what the PDF parser extracts:
- Text content
- Tables
- Metadata (page count, title, etc.)

Usage:
    python scripts/test_pdf_parser.py
    python scripts/test_pdf_parser.py --output extracted_text.txt  # Save to file
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pdf_parser import PdfParserService


def main():
    """Test PDF parser on DHL Express API docs."""
    parser = argparse.ArgumentParser(description="Test PDF parser extraction")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file to save extracted text (default: output/dhl_extracted_text.txt)",
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default=None,
        help="PDF file to parse (default: examples/dhl_express_api_docs.pdf)",
    )
    args = parser.parse_args()

    # Determine PDF path
    if args.pdf:
        pdf_path = Path(args.pdf)
    else:
        pdf_path = (
            Path(__file__).parent.parent / "examples" / "dhl_express_api_docs.pdf"
        )

    if not pdf_path.exists():
        print(f"❌ Error: PDF not found: {pdf_path}")
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        # Default: output/dhl_extracted_text.txt
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "dhl_extracted_text.txt"

    print("=" * 70)
    print("PDF Parser Test - DHL Express API Documentation")
    print("=" * 70)
    print()

    pdf_parser = PdfParserService()

    # 1. Extract metadata
    print("📊 Step 1: Extracting metadata...")
    print("-" * 70)
    try:
        metadata = pdf_parser.extract_metadata(str(pdf_path))
        print(f"   Page count: {metadata.get('page_count', 'N/A')}")
        file_size = metadata.get("file_size", 0)
        if file_size:
            print(
                f"   File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)"
            )
        else:
            print(f"   File size: N/A")
        print(f"   Title: {metadata.get('title', 'N/A')}")
        print(f"   Author: {metadata.get('author', 'N/A')}")
        print(f"   Created: {metadata.get('created', 'N/A')}")
        print()
    except Exception as e:
        print(f"   ❌ Error extracting metadata: {e}")
        print()

    # 2. Extract text (sample from beginning)
    print("📄 Step 2: Extracting text content...")
    print("-" * 70)
    print("   Note: This is a large PDF (234+ pages). Extracting sample...")
    try:
        # Extract text from entire PDF (this may take a moment)
        text = pdf_parser.extract_text(str(pdf_path))
        print(f"   ✅ Extracted {len(text):,} characters from PDF")
        print()
        print("   Preview (first 800 characters):")
        print("   " + "-" * 66)
        preview = text[:800].replace("\n", "\n   ")
        print(f"   {preview}")
        if len(text) > 800:
            print("   ...")
            print(
                f"   (Total: {len(text):,} characters from {metadata.get('page_count', '?')} pages)"
            )
        print()

        # Save to file (always save, default location is output/)
        output_path.write_text(text, encoding="utf-8")
        print(f"   💾 Saved extracted text to: {output_path}")
        print(f"   File size: {output_path.stat().st_size:,} bytes")
        print()
    except Exception as e:
        print(f"   ❌ Error extracting text: {e}")
        print()

    # 3. Extract tables (if any)
    print("📋 Step 3: Extracting tables...")
    print("-" * 70)
    try:
        # Create parser with table extraction enabled
        parser_with_tables = PdfParserService(config={"extract_tables": True})
        # Extract text with tables (this will include table data)
        text_with_tables = parser_with_tables.extract_text(str(pdf_path))

        # Check if tables were found (they'd be marked with [Table on page X])
        if "[Table" in text_with_tables:
            print("   ✅ Tables detected in PDF")
            # Count how many tables
            table_count = text_with_tables.count("[Table")
            print(f"   Found {table_count} tables")

            # Show a sample table section
            lines = text_with_tables.split("\n")
            table_sections = []
            in_table = False
            for i, line in enumerate(lines):
                if "[Table" in line:
                    in_table = True
                    table_sections.append((i, line))
                elif in_table and line.strip() and not line.startswith("["):
                    table_sections.append((i, line))
                    if len(table_sections) > 10:  # Show first few lines of first table
                        break

            if table_sections:
                print("   Sample table content:")
                for _, line in table_sections[:8]:
                    print(f"   {line[:80]}")
        else:
            print("   ℹ️  No tables detected (or tables not in tabular format)")
            print("   (Tables may be embedded as images or in non-tabular format)")
        print()
    except Exception as e:
        print(f"   ❌ Error extracting tables: {e}")
        print()

    # 4. Show what we can do with this extracted text
    print("🎯 Step 4: What can we do with this extracted text?")
    print("-" * 70)
    print("   The extracted text can now be sent to an LLM to:")
    print("   • Extract API endpoints (GET /api/track, POST /api/ship, etc.)")
    print("   • Extract request/response schemas")
    print("   • Extract authentication methods")
    print("   • Extract business rules and constraints")
    print("   • Generate mapper code automatically")
    print()
    print("=" * 70)
    print("✅ PDF Parser test complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
