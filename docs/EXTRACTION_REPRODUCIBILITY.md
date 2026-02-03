# Determinism & Reproducibility in LLM Extraction

Extraction outputs can vary between runs (different model, temperature, or prompt wording). This doc describes how we record config and prompt versions so you can reproduce or regression-test extraction.

## Output metadata: `extraction_metadata`

Every schema.json (or API `/extract` response) written by the extraction pipeline includes optional **`extraction_metadata`** when available:

- **`llm_config`** — LLM settings used for the run:
  - **`model`** — e.g. `gpt-4.1-mini`
  - **`temperature`** — e.g. `0.0` (deterministic)
  - **`top_p`** — if set
  - **`response_format`** — e.g. `{"type": "json_object"}` when JSON mode is used

- **`prompt_versions`** — Version of each prompt group used:
  - **`schema`** — schema extraction prompt (e.g. `"1.0"`)
  - **`field_mappings`** — field mappings prompt
  - **`constraints`** — constraints prompt
  - **`edge_cases`** — edge cases prompt

Example:

```json
{
  "schema_version": "1.0.0",
  "generator_version": "0.1.0",
  "schema": { ... },
  "field_mappings": [ ... ],
  "constraints": [ ... ],
  "edge_cases": [ ... ],
  "extraction_metadata": {
    "llm_config": {
      "model": "gpt-4.1-mini",
      "temperature": 0.0,
      "response_format": { "type": "json_object" }
    },
    "prompt_versions": {
      "schema": "1.0",
      "field_mappings": "1.0",
      "constraints": "1.0",
      "edge_cases": "1.0"
    }
  }
}
```

Use this to:

- Reproduce a run (same model, temperature, prompt versions).
- Debug “why did output change?” (compare `llm_config` and `prompt_versions` between runs).
- Regression-test: assert that for fixed input + fixed config, output matches expected (see Golden tests below).

## Prompt versions

Prompts live in **`src/prompts/extraction_prompts.py`**. Each group has a version constant:

- **`PROMPT_VERSION_SCHEMA`** — schema extraction
- **`PROMPT_VERSION_FIELD_MAPPINGS`** — field mappings
- **`PROMPT_VERSION_CONSTRAINTS`** — constraints
- **`PROMPT_VERSION_EDGE_CASES`** — edge cases

**When to bump:** Change the constant when you change prompt *content* or *structure* in a way that can change extraction output (e.g. new instructions, different JSON shape). That way `prompt_versions` in the output reflects what was actually used and tooling can warn when versions differ.

**API:** **`get_prompt_versions()`** returns a dict of all current prompt versions; the pipeline calls it and stores the result in `extraction_metadata.prompt_versions`.

## LLM config

The extractor (**`LlmExtractorService`**) stores model, temperature, and optional `model_kwargs` (e.g. `response_format`, `top_p`). **`get_config()`** returns a dict suitable for `extraction_metadata.llm_config`. The pipeline calls it when saving output so every written schema.json records the LLM settings used.

## Extracted text persistence

When parsing from a PDF, the pipeline **always saves extracted text** (default: `output/<pdf_stem>_extracted_text.txt`) before the LLM step. Use `--extracted-text <path>` to re-run with that file and skip PDF parsing—useful for reproducibility when testing different models or prompts on the same input.

## Golden tests

We use **golden tests** to lock down extraction for a fixed input and fixed LLM responses:

1. **Fixed extracted text** — **`tests/fixtures/golden_extracted_text.txt`** is a short, fixed snippet of “extracted” PDF text.
2. **Mocked LLM** — The test mocks the LLM to return fixed schema, field_mappings, constraints, and edge_cases (and **`get_config()`**).
3. **Pipeline run** — The pipeline runs with **`extracted_text_path`** pointing at the fixture (no real PDF or API call).
4. **Assertions** — The test asserts:
   - **Contract fields:** `schema_version`, `generator_version`.
   - **Reproducibility:** `extraction_metadata` is present with `llm_config` (model, temperature) and `prompt_versions`.
   - **Schema invariants:** e.g. `schema.name`, `schema.base_url`, number of endpoints, structure of `field_mappings` and `edge_cases`.
   - **Optional:** Key fields match a saved **golden expected JSON** (**`tests/fixtures/golden_expected_schema.json`**) so we can detect unintended changes (e.g. after prompt or code changes).

**Where:** **`tests/integration/test_extraction_golden.py`**

- **`test_golden_extraction_invariants`** — Asserts extraction_metadata and key invariants.
- **`test_golden_extraction_matches_expected_json`** — Compares key invariants to `golden_expected_schema.json` (skips if file missing).

**Running golden tests:**

```bash
docker compose run --rm app pytest tests/integration/test_extraction_golden.py -v
```

**Updating the golden expected file:** If you intentionally change schema shape or extraction_metadata (e.g. new prompt version), re-run extraction with the same fixture and mock, then copy the relevant keys into **`tests/fixtures/golden_expected_schema.json`** (or regenerate and commit).

## Summary

| What | Where | Purpose |
|------|--------|--------|
| **extraction_metadata** | schema.json, API /extract response | Record LLM config + prompt versions for reproducibility |
| **Prompt version constants** | `src/prompts/extraction_prompts.py` | Bump when prompt content/structure changes |
| **get_prompt_versions()** | `src/prompts/extraction_prompts.py` | Expose current prompt versions to pipeline |
| **get_config()** | `src/llm_extractor.py` | Expose LLM model, temperature, top_p, response_format to pipeline |
| **Golden tests** | `tests/integration/test_extraction_golden.py`, `tests/fixtures/` | Regression test: fixed text + mocked LLM → assert output shape and extraction_metadata |
