# Brief Score and Improvements

This document scores the project against the "Carrier Doc Parser" brief (messy PDF + LLM → standardized JSON schema matching Universal Carrier Format) and lists concrete improvements to raise the score.

---

## Scoring Rubric

| Criterion | Scale | Description |
|-----------|-------|-------------|
| **Fit to brief** | 1–5 | Does it take a messy PDF, use an LLM (LangChain or similar), and output standardized JSON matching a Universal Carrier Format? |
| **Code quality & structure** | 1–5 | Clear separation of concerns, types, error handling, and maintainability. |
| **Testing** | 1–5 | Unit and integration coverage for the parser pipeline; mocks for LLM. |
| **Documentation** | 1–5 | README, run instructions, and explanation of output format. |
| **Extensibility** | 1–5 | Easy to add carriers, change models, or extend the schema. |

Scale: 1 = Poor, 2 = Fair, 3 = Good, 4 = Very Good, 5 = Excellent.

---

## Score per Criterion

### 1. Fit to brief — 5/5 (Excellent)

- **Messy PDF input:** CLI `python -m src.formatter <pdf> -o output/schema.json`; `src/pdf_parser.py` (pdfplumber + pymupdf) extracts text; example PDF: `examples/dhl_express_api_docs.pdf`.
- **LLM (LangChain):** `src/llm_extractor.py` uses `langchain_openai.ChatOpenAI`; dependencies in `pyproject.toml`: `langchain`, `langchain-openai`, `langchain-anthropic`.
- **Parse and output:** `ExtractionPipeline` in `src/extraction_pipeline.py` orchestrates PDF → text → LLM → validation → JSON; output includes `schema`, `field_mappings`, `constraints`, `edge_cases`, plus `schema_version` and `generator_version`.
- **Universal Carrier Format:** `src/core/schema.py` defines `UniversalCarrierFormat` (Pydantic); output JSON conforms; `examples/expected_output.json` and `docs/schema_contract_meta_schema.json` document the contract.

### 2. Code quality & structure — 4/5 (Very Good)

- Clear pipeline: `formatter.py` → `ExtractionPipeline` → `PdfParserService`, `LlmExtractorService`, `CarrierValidator`; prompts in `src/prompts/extraction_prompts.py`.
- Pydantic models for schema and validation; type hints used across core and API.
- Some long methods in `llm_extractor.py` (multi-step extraction); could be split for readability.
- Consistent style: black, isort, flake8; config in `pyproject.toml`.

### 3. Testing — 4/5 (Very Good)

- Unit tests: `test_llm_extractor.py` (mocked ChatOpenAI), `test_pdf_parser.py`, `test_validator.py`, `test_carrier_schema.py`.
- Integration: `test_extraction_pipeline.py` (mocked LlmExtractorService), `test_extraction_golden.py` (fixed input + mocked LLM), `test_formatter_cli.py` (mocked ExtractionPipeline).
- No test that runs the formatter end-to-end on a real (small) PDF file with mocked LLM; would strengthen "parser" demo.

### 4. Documentation — 5/5 (Excellent)

- README describes PDF extraction, Universal Carrier Format, formatter CLI, and conversion flow; links to `HOW_TO_MAKE_MAPPER_FROM_PDF.md`, `EXTRACTION_REPRODUCIBILITY.md`, and others.
- `docs/LLM_EXTRACTION_FLOW.md`, `docs/EXTRACTION_REPRODUCIBILITY.md`, and schema contract/meta-schema cover behaviour and reproducibility.
- One-command run: `docker-compose run --rm app python -m src.formatter examples/dhl_express_api_docs.pdf -o output/schema.json`.

### 5. Extensibility — 5/5 (Excellent)

- Registry/plugin architecture: `CarrierMapperBase` / `CarrierAbstract`, `@register_carrier`, `CarrierRegistry`; one mapping file per carrier; see `docs/ADDING_A_CARRIER.md`.
- Configurable LLM model and options (e.g. `--llm-model`, temperature, JSON mode); extraction metadata records config for reproducibility.
- Blueprint path as alternative to PDF; mapper generator produces code from schema JSON.

---

## Overall Score

**92/100 (Very Good / Excellent).**

The project fully satisfies the brief: it takes a messy carrier API PDF, uses a Python pipeline with LangChain (OpenAI) to parse it, and outputs a standardized JSON schema that matches the Universal Carrier Format (Pydantic-backed, validated). It goes beyond a minimal "few hours" script by adding a clear pipeline, validation, versioning, tests (unit + integration with mocks), strong documentation, and an extensible carrier/mapper design. Minor gaps: no single-file "run this script" entry point for reviewers who expect literally one script, and no end-to-end test that runs the formatter on a real PDF path (with mocked LLM).

---

## Pipeline (overview)

```mermaid
flowchart LR
    PDF[Input PDF]
    PdfParser[PdfParserService]
    Text[Extracted text]
    LlmExtractor[LlmExtractorService]
    Validator[CarrierValidator]
    JSON[Output JSON]

    PDF --> PdfParser
    PdfParser --> Text
    Text --> LlmExtractor
    LlmExtractor --> Validator
    Validator --> JSON
```

---

## Improvements to Raise the Score

### Fit to brief

1. **One-file runnable script:** Add `scripts/run_parser.py` (or similar) that accepts a PDF path and output path, calls the extraction pipeline, and writes JSON. Document it as "the Carrier Doc Parser script" so reviewers can run one file if they expect "a Python script."

### Code quality

2. **Refactor long LLM methods:** Split the large extraction methods in `src/llm_extractor.py` into smaller functions (e.g. per extraction step) to improve readability and testability.

3. **Centralize magic strings:** Replace repeated strings (e.g. model names, prompt keys) with constants or a small config module where it reduces drift and typos.

### Testing

4. **End-to-end parser test:** Add one integration test that runs the formatter on a small real PDF (e.g. a fixture under `tests/fixtures/`) with the LLM mocked, and asserts the output JSON has the expected top-level keys and a valid `schema` shape. This demonstrates "run parser on PDF → get UCF JSON" in CI.

5. **LLM failure behaviour:** Add tests for LLM timeout, malformed JSON response, or API errors to ensure the pipeline fails clearly and does not leave partial output.

### Documentation

6. **"Quick start for the brief" in README:** Add a short section (e.g. "Carrier Doc Parser (brief)") with one command: PDF in, JSON out (and where to set `OPENAI_API_KEY`). Makes alignment to the brief obvious.

### Extensibility

7. **Anthropic / multi-provider:** Document or implement use of `langchain-anthropic` (e.g. env-driven provider or `--provider openai|anthropic`) so the brief’s "LangChain or similar" is clearly multi-provider capable.

8. **Schema version in README:** Mention `schema_version` and `generator_version` in the "Output" description so reviewers see that the JSON is versioned and toolable.

---

## Summary

| Criterion | Score | Note |
|-----------|-------|------|
| Fit to brief | 5/5 | PDF → LLM → UCF JSON; LangChain; single command. |
| Code quality & structure | 4/5 | Clear pipeline; some long methods. |
| Testing | 4/5 | Good mocks; add one E2E PDF test. |
| Documentation | 5/5 | README, guides, contract. |
| Extensibility | 5/5 | Registry, configurable LLM, blueprints. |
| **Overall** | **92/100** | Strong match to brief; small improvements above. |
