# Schema migration guide

When `schema_version` (or the generator) changes, downstream tools and hand-crafted schemas may need updates. This guide describes how to detect and handle schema migrations.

## Version fields in output

- **`schema_version`** — Contract format version of the output JSON (e.g. `"1.0.0"`). Defined in `src/core/contract.py` (`SCHEMA_VERSION`). When we add or change top-level keys or the shape of `schema`, `field_mappings`, `constraints`, or `edge_cases`, this may be bumped.
- **`generator_version`** — Version of the tool that produced the file (e.g. from `pyproject.toml` or `get_generator_version()`). Useful for “which formatter run produced this?”.

## When `schema_version` is bumped

1. **Re-run the parser/formatter**  
   Re-extract from the same PDF (or blueprint) so the new `schema.json` matches the current contract. Old files may still load if the change is additive and your code ignores unknown keys.

2. **Re-run the mapper generator**  
   If you generate mapper code from `schema.json`, run the mapper generator again so the generated code matches the new schema shape:
   ```bash
   python -m src.mapper_generator_cli output/schema.json -o src/mappers/carrier_mapper.py
   ```

3. **Update validators**  
   If you use generated constraint validators (`*_validators.py`), regenerate them (run the formatter/run_parser again with validators enabled) and update any imports or mixins that depend on the old constraint shape.

4. **Validate existing files**  
   Use the validate-only script to check that old or hand-edited `schema.json` files still conform (required keys + UCF schema):
   ```bash
   python scripts/validate_schema.py path/to/schema.json
   ```
   If the contract has been tightened, some old files may fail validation and need to be re-extracted or updated by hand.

## Detecting and upgrading old schema files

- **Detect version:** Read `schema_version` (and optionally `generator_version`) from the JSON. Compare to the current `SCHEMA_VERSION` in code or to your minimum supported version.
- **Upgrade strategy:** Prefer re-running the extraction pipeline (PDF or blueprint → schema) over hand-editing. For hand-crafted schemas, apply the same structure as the current formatter output (see `docs/schema_contract_meta_schema.json` and `examples/expected_output.json`).
- **Breaking changes:** If we ever remove or rename top-level keys or change UCF model fields, release notes or CHANGELOG will describe the migration; update readers and the validate script accordingly.

## Related

- **Contract and meta-schema:** `docs/schema_contract_meta_schema.json`
- **Validate-only mode:** `scripts/validate_schema.py [path/to/schema.json]`
- **Output description:** README “Output” section (versioned and toolable)
