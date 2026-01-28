#!/usr/bin/env python3
"""
Scan extracted PDF text for exception/edge-case content and verify the LLM schema.

1. Scans dhl_extracted_text.txt (or given path) for exception-related patterns:
   surcharge, restriction, error, customs, limitation, remote area, edge case, etc.
2. Loads the LLM-converted schema and checks edge_cases (and endpoint error responses)
   for presence of that content.

Usage:
    python scripts/check_exceptions_in_extraction.py
    python scripts/check_exceptions_in_extraction.py --extracted-text output/dhl_extracted_text.txt --schema output/dhl_express_api_schema.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Patterns that indicate exception/edge-case content in carrier docs (Scenario 3)
EXCEPTION_PATTERNS = [
    (r"\bsurcharge\b", "surcharge"),
    (r"\brestriction\b", "restriction"),
    (r"\berror\s*(code|message|list|appendix)?\b", "error"),
    (r"\bcustoms\b", "customs"),
    (r"\blimitation\b", "limitation"),
    (r"\bremote\s+area\b", "remote area"),
    (r"\bedge\s*case\b", "edge case"),
    (r"\bexception\b", "exception"),
    (r"\bwarning\b", "warning"),
    (r"\bCREATESHIPMENT\s+ERRORS\b", "CREATESHIPMENT ERRORS"),
    (r"\bRATEREQUEST\s+.*ERRORS\b", "RATEREQUEST errors"),
    (r"\bFuel\s+Surcharge\b", "Fuel Surcharge"),
    (r"\bSCH\s*=\s*Surcharge\b", "SCH = Surcharge"),
]


def scan_text_for_exceptions(text_path: Path) -> dict:
    """Scan extracted text for exception-related patterns. Return counts and sample lines."""
    if not text_path.exists():
        return {
            "error": f"File not found: {text_path}",
            "patterns": {},
            "total_lines": 0,
        }

    content = text_path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()
    total_lines = len(lines)

    pattern_counts: dict[str, list[str]] = {}
    for pattern, label in EXCEPTION_PATTERNS:
        regex = re.compile(pattern, re.IGNORECASE)
        matches: list[str] = []
        for i, line in enumerate(lines):
            if regex.search(line):
                # Store a short sample (first 100 chars of line)
                sample = line.strip()[:100]
                if sample and sample not in matches:
                    matches.append(sample)
                    if len(matches) >= 5:  # Cap samples per pattern
                        break
        if matches:
            pattern_counts[label] = matches

    return {
        "path": str(text_path),
        "total_lines": total_lines,
        "patterns": pattern_counts,
        "summary": f"Found exception-related content: {len(pattern_counts)} pattern types, sample lines collected.",
    }


def load_schema_and_check_edge_cases(schema_path: Path) -> dict:
    """Load schema JSON and report edge_cases and endpoint error responses."""
    if not schema_path.exists():
        return {
            "error": f"File not found: {schema_path}",
            "edge_cases": [],
            "error_responses": [],
        }

    try:
        data = json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {"error": str(e), "edge_cases": [], "error_responses": []}

    edge_cases = data.get("edge_cases") or []
    schema_obj = data.get("schema") or {}
    endpoints = schema_obj.get("endpoints") or []
    error_responses: list[dict] = []
    for ep in endpoints:
        path = ep.get("path", "")
        summary = ep.get("summary", "")
        for resp in ep.get("responses") or []:
            code = resp.get("status_code")
            if code is not None and code >= 400:
                error_responses.append(
                    {"path": path, "summary": summary, "status_code": code}
                )

    return {
        "path": str(schema_path),
        "edge_cases": edge_cases,
        "edge_cases_count": len(edge_cases),
        "error_responses": error_responses,
        "schema_name": schema_obj.get("name"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan extracted text for exceptions and check schema edge_cases."
    )
    parser.add_argument(
        "--extracted-text",
        type=Path,
        default=Path(__file__).parent.parent / "output" / "dhl_extracted_text.txt",
        help="Path to extracted PDF text file",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).parent.parent / "output" / "dhl_express_api_schema.json",
        help="Path to LLM-generated schema JSON",
    )
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    text_path = (
        args.extracted_text
        if args.extracted_text.is_absolute()
        else root / args.extracted_text
    )
    schema_path = args.schema if args.schema.is_absolute() else root / args.schema

    print("=" * 70)
    print("Exception / edge-case check: extracted text vs schema")
    print("=" * 70)
    print()

    # 1. Scan extracted text
    print("1. Scanning extracted text for exception-related content")
    print("-" * 70)
    scan = scan_text_for_exceptions(text_path)
    if "error" in scan:
        print(f"   ❌ {scan['error']}")
    else:
        print(f"   File: {scan['path']}")
        print(f"   Total lines: {scan['total_lines']}")
        print(f"   {scan['summary']}")
        for label, samples in scan.get("patterns", {}).items():
            print(f"   - {label}: {len(samples)} sample line(s)")
            for s in samples[:2]:
                print(f'     "{s}..."' if len(s) >= 100 else f'     "{s}"')
    print()

    # 2. Check schema edge_cases and error responses
    print("2. Schema edge_cases and error responses")
    print("-" * 70)
    schema_report = load_schema_and_check_edge_cases(schema_path)
    if "error" in schema_report:
        print(f"   ❌ {schema_report['error']}")
    else:
        print(f"   Schema: {schema_report['path']}")
        print(f"   Name: {schema_report.get('schema_name', 'N/A')}")
        print(f"   edge_cases count: {schema_report['edge_cases_count']}")
        if schema_report["edge_cases"]:
            for i, ec in enumerate(schema_report["edge_cases"][:5]):
                print(
                    f"     [{i}] {ec.get('type', '')} - {ec.get('requirement', ec.get('route', str(ec)))[:60]}"
                )
        else:
            print("   edge_cases: (empty)")
        print(
            f"   Endpoint error responses (4xx/5xx): {len(schema_report['error_responses'])}"
        )
        for er in schema_report["error_responses"][:5]:
            print(f"     {er['path']} -> {er['status_code']}")
    print()

    # 3. Verdict
    print("3. Verdict")
    print("-" * 70)
    if "error" in scan or "error" in schema_report:
        print("   Skipped (missing file or invalid JSON).")
    else:
        has_text_exceptions = bool(scan.get("patterns"))
        has_schema_edge_cases = schema_report.get("edge_cases_count", 0) > 0
        if has_text_exceptions and not has_schema_edge_cases:
            print(
                "   ⚠️  Extracted text contains exception/edge-case content, but schema edge_cases is empty."
            )
            print(
                "   Consider re-running the formatter (e.g. with --extracted-text) to repopulate edge_cases."
            )
        elif has_text_exceptions and has_schema_edge_cases:
            print(
                "   ✅ Extracted text has exception content and schema has edge_cases."
            )
        elif not has_text_exceptions:
            print(
                "   ℹ️  No exception-related patterns found in extracted text (or file missing)."
            )
        else:
            print("   ✅ Schema has edge_cases.")
    print()


if __name__ == "__main__":
    main()
