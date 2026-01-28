#!/usr/bin/env python3
"""
Debug script: run field-mappings extraction and print result.

Use this to investigate why field_mappings is empty in the schema.
With --verbose, enables DEBUG logging (e.g. unwrap messages). Use --max-chars
to send less text and get a faster response.

Usage:
    python scripts/debug_field_mappings.py
    python scripts/debug_field_mappings.py --max-chars 20000 --verbose
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm_extractor import LlmExtractorService  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Debug field-mappings extraction")
    parser.add_argument(
        "--text",
        type=Path,
        default=Path(__file__).parent.parent / "output" / "dhl_extracted_text.txt",
        help="Path to extracted PDF text file",
    )
    parser.add_argument(
        "--carrier",
        default="MYDHL",
        help="Carrier name for the prompt",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=None,
        help="Use only first N chars of text (faster); default: use all",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable DEBUG logging",
    )
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    text_path = args.text if args.text.is_absolute() else root / args.text
    if not text_path.exists():
        print(f"Error: file not found: {text_path}")
        sys.exit(1)

    pdf_text = text_path.read_text(encoding="utf-8", errors="replace")
    if args.max_chars:
        pdf_text = pdf_text[: args.max_chars]
        print(f"Using first {args.max_chars} chars.")
    print(f"Text length: {len(pdf_text)} chars\n")

    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG, format="%(name)s %(levelname)s %(message)s"
        )

    extractor = LlmExtractorService()
    mappings = extractor.extract_field_mappings(pdf_text, args.carrier)

    print("--- field_mappings result ---")
    print(f"Count: {len(mappings)}")
    if mappings:
        print(json.dumps(mappings[:5], indent=2))
        if len(mappings) > 5:
            print(f"... and {len(mappings) - 5} more")
    else:
        print(
            "(empty). Run with -v to see DEBUG logs, or check WARNING for dict keys if LLM returned an object."
        )


if __name__ == "__main__":
    main()
