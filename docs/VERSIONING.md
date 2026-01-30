# How we version

This project uses versioning in three places: the app, the schema contract, and the changelog.

## Application version

- **Source:** `pyproject.toml` → `[project] version` (e.g. `0.1.0`).
- **Use:** Shown in API responses and in `generator_version` in schema JSON output so downstream tools know which formatter run produced a file.
- **When to bump:** On releases or notable feature/breaking changes (see CHANGELOG).

## Schema contract version

- **Source:** `src/core/contract.py` → `SCHEMA_VERSION` (e.g. `"1.0.0"`).
- **Use:** Written as `schema_version` in every schema JSON file. Downstream tools (mapper generator, validators) can detect contract changes and trigger migrations.
- **When to bump:** When the **output contract** changes (new/removed top-level keys, or changes to the shape of `schema`, `field_mappings`, `constraints`, `edge_cases`). See [SCHEMA_MIGRATION.md](SCHEMA_MIGRATION.md).

## Changelog

- **File:** [CHANGELOG.md](../CHANGELOG.md) at project root.
- **Format:** Reverse chronological (newest first). Each entry: date, brief description, and bullet list of Added/Fixed/Changed.
- **When to update:** With every notable commit or release. The pre-commit hook reminds you to update CHANGELOG when it’s not included in the commit.

## Summary

| What              | Where                 | Used for                          |
|-------------------|-----------------------|-----------------------------------|
| App version       | `pyproject.toml`      | Releases, `generator_version`     |
| Schema version    | `src/core/contract.py`| Contract compatibility, migration |
| Changelog         | `CHANGELOG.md`        | Human-readable release history    |
