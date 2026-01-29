#!/usr/bin/env python3
"""
Carrier Doc Parser script — one-file entry point for PDF → Universal Carrier Format JSON.

Accept a PDF path and (optional) output path; run the extraction pipeline and write
the schema JSON. For reviewers who expect "a Python script" to parse carrier docs:

    python scripts/run_parser.py path/to/carrier_docs.pdf
    python scripts/run_parser.py path/to/carrier_docs.pdf -o output/schema.json

Requires OPENAI_API_KEY in the environment (or .env). Run from project root.
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is on path when run as scripts/run_parser.py
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env")

from src.core.config import DEFAULT_LLM_MODEL  # noqa: E402
from src.extraction_pipeline import ExtractionPipeline  # noqa: E402


def _progress(step: str, message: str) -> None:
    print(f"  [{step}] {message}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Carrier Doc Parser: extract Universal Carrier Format JSON from a carrier API PDF."
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to the carrier API documentation PDF",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: output/<pdf_stem>_schema.json)",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default=None,
        help=f"LLM model (default: provider-specific, e.g. {DEFAULT_LLM_MODEL})",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "anthropic"],
        default=None,
        help="LLM provider: openai or anthropic (default: LLM_PROVIDER env or openai)",
    )
    args = parser.parse_args()

    pdf_path = args.pdf_path.resolve()
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output
    if output_path is None:
        output_path = _ROOT / "output" / f"{pdf_path.stem}_schema.json"
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Carrier Doc Parser")
    print("  PDF:", pdf_path)
    print("  Output:", output_path)
    print()

    pipeline = ExtractionPipeline(
        llm_model=args.llm_model,
        provider=args.provider,
    )
    pipeline.process(
        str(pdf_path),
        output_path=str(output_path),
        progress_callback=_progress,
        generate_validators=True,
    )
    print()
    print("Done. Schema written to:", output_path)


if __name__ == "__main__":
    main()
