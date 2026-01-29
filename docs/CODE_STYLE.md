# Code Style & Conventions

This document maps common Python style feedback to this project’s current state and conventions. Use it when contributing or reviewing code.

---

## 1. PEP 8 and Code Style

| Feedback | Our status |
|----------|------------|
| **Function/variable naming** — Prefer `snake_case` (e.g. `format_address`), not camelCase. | ✅ We use `snake_case` for functions and variables across `src/`. |
| **Module/file naming** — Use `snake_case` (e.g. `carrier_formatter.py`). | ✅ Module names are snake_case: `formatter.py`, `api.py`, `openapi_generator.py`, etc. |
| **Class naming** — CamelCase (e.g. `CarrierFormatter`). | ✅ Classes use CamelCase: `UniversalCarrierFormat`, `ExtractionPipeline`, etc. |
| **Indentation** — 4 spaces; avoid excess blank lines. | ✅ We use 4 spaces. Formatting is enforced by **black** (pre-commit and CI). |
| **Whitespace** | **black** and **flake8** in pre-commit keep style consistent. |

---

## 2. Documentation

| Feedback | Our status |
|----------|------------|
| **Module/class/method docstrings** — Public APIs should have docstrings (purpose, params, return). | ✅ Key modules have file-level docstrings (`api.py`, `formatter.py`, `llm_extractor.py`, `extraction_pipeline.py`, etc.). Method coverage varies; add docstrings for new public functions and classes. |
| **File-level docstrings** | ✅ Present at top of main modules. Add a one-line summary (and optionally usage) for new modules. |

---

## 3. Imports

| Feedback | Our status |
|----------|------------|
| **Clean, explicit imports; no unused imports.** | ✅ `import os` and `import sys` are used where present (`os.getenv`, `sys.exit` in CLIs). Remove any unused imports if you see them. |
| **Style** | **isort** in pre-commit keeps import order consistent. |

---

## 4. Type Hints

| Feedback | Our status |
|----------|------------|
| **Type annotations** — Improve clarity and work with type-checkers. | ✅ Public entry points and key modules use type hints (e.g. `formatter.main` → `None`, `extraction_pipeline.process` progress_callback `Callable[[str, str], None]`, CLI `main` → `None`). Add types for new public functions. |
| **Checking** | CI runs two steps: (1) **full** `mypy src/` — non-blocking, with a visible fail-count summary; (2) **strict** `mypy src/core/` — blocking (must pass). Config: `[tool.mypy]` in `pyproject.toml`. Locally: `make type-check` (full) or `docker compose run --rm app mypy src/core/` (strict). |

---

## 5. Exception Handling

| Feedback | Our status |
|----------|------------|
| **Prefer specific exceptions** (e.g. `ValueError`, `OSError`) over bare `Exception`. | ✅ API, formatter, CLIs, llm_extractor, pdf_parser, mappers, blueprints/converter, and mapper_generator catch or raise specific types first (`ValueError`, `OSError`, `KeyError`, `TypeError`, `ValidationError`, `json.JSONDecodeError`); broad `Exception` is used only as fallback or for intentional catch-all (e.g. CLI “unexpected error”). |
| **Avoid broad `except Exception`** unless re-raising or logging and re-raising. | Specific handlers are documented in code; remaining broad catches are limited to fallbacks and debug paths. |

---

## 6. Constants

| Feedback | Our status |
|----------|------------|
| **Constant naming** — UPPER_SNAKE_CASE; group at top of file. | ✅ We use UPPER_SNAKE where we have constants. New constants: put at module or class top and use UPPER_SNAKE. |

---

## 7. Testing

| Feedback | Our status |
|----------|------------|
| **Test naming** — Use descriptive names; prefer snake_case. | ✅ Tests use `test_*` and snake_case (e.g. `test_convert_success`). |
| **Assertions** — Prefer `self.assertEqual`, `self.assertRaises` in unittest. | ✅ We use **pytest**; plain `assert` is the idiomatic style. No need to switch to unittest-style assertions. |
| **Test structure** — Clear separation; fixtures where appropriate. | ✅ `tests/unit/` and `tests/integration/`; `conftest.py` for shared fixtures; `setUp`/fixtures used where needed. |

---

## 8. CLI conventions

| Convention | Status |
|------------|--------|
| **Framework** — Use **Click** for all CLIs. | ✅ `formatter`, `blueprints.cli`, `mapper_generator_cli`, `openapi_generator` use Click. |
| **Common options** — Use `--output` / `-o` for output path, `--verbose` / `-v` for verbose logging. | ✅ All four CLIs support `-o, --output` and `-v, --verbose`. Formatter also has `--no-validators` where applicable. |
| **Entry points** — Run as `python -m src.<module>`. CI runs `python -m src.<module> --help` smoke tests to catch broken entry points. | ✅ See `.github/workflows/tests.yml` step "CLI --help smoke tests". |

---

## 9. Logging

| Feedback | Our status |
|----------|------------|
| **No `print` for debugging**; use `logging` for operational/debug output. | ✅ CLI and services use `logging`; no stray `print` in library code. Use `logger = logging.getLogger(__name__)` in new modules. |

---

## 10. General Pythonic Patterns

| Feedback | Our status |
|----------|------------|
| **`@property`** for read-only attributes. | Use where it improves clarity (e.g. schema/model attributes). |
| **List comprehensions** — Prefer for simple iterations. | Use when readable; no strict rule. |

---

## 11. Dependency Management

| Feedback | Our status |
|----------|------------|
| **Dependencies** — Single source of truth. | ✅ `pyproject.toml` (dependencies + optional `dev`); pinned in `uv.lock`. Docker and CI install from the same lockfile. |
| **`.gitignore`** — Python artifacts, venv, etc. | ✅ Includes `__pycache__/`, `*.py[cod]`, `.venv/`, `.env`, `.pytest_cache/`, `htmlcov/`, and project-specific paths. |

---

## 12. Project Structure

| Feedback | Our status |
|----------|------------|
| **Package layout** — Main code in a package directory. | ✅ Application code lives under `src/` (e.g. `src/api.py`, `src/formatter.py`, `src/blueprints/`, `src/mappers/`). Scripts in `scripts/`, docs in `docs/`. |

---

## 13. README and Documentation

| Feedback | Our status |
|----------|------------|
| **README** — Usage, installation, contribution, examples. | ✅ README covers installation (Docker), usage (formatter, blueprint, mapper demo, API), testing, documentation links, and pointers to `docs/` (testing, onboarding, development pipeline, Docker). See [TESTING.md](TESTING.md), [ONBOARDING.md](ONBOARDING.md), [DEVELOPMENT_PIPELINE.md](DEVELOPMENT_PIPELINE.md). |

---

## Quick reference for contributors

- **Format/lint:** `black`, `isort`, `flake8` (run via pre-commit or `make`/docker).
- **Naming:** `snake_case` (functions, variables, modules), `CamelCase` (classes).
- **Docstrings:** Add for new public modules, classes, and functions.
- **Types:** Add type hints for new code when straightforward.
- **Exceptions:** Prefer specific exceptions when you touch error paths.
- **Tests:** pytest; use `assert` and fixtures; keep tests in `tests/unit/` or `tests/integration/`.
