# Test Coverage Review

**Date:** 2026-01-26  
**Overall Coverage:** 71% (535 statements, 156 missing)

## Coverage Summary by Module

| Module | Coverage | Missing Lines | Status |
|--------|----------|---------------|--------|
| `src/core/schema.py` | 98% | 213, 461 | ✅ Excellent |
| `src/pdf_parser.py` | 98% | 301, 324 | ✅ Excellent |
| `src/extraction_pipeline.py` | 100% | - | ✅ Perfect |
| `src/llm_extractor.py` | 72% | 135-145, 148-149, 229-235, 246-248, 294-301, 354-356 | ⚠️ Needs work |
| `src/mappers/dpd_mapper.py` | 53% | 124-126, 155, 171, 188-236, 241-251, 255-268 | ⚠️ Needs work |
| `src/core/validator.py` | 26% | 58-62, 79-85, 104-119 | ❌ Critical gap |
| `src/formatter.py` | 0% | 14-114 | ❌ Critical gap |
| `src/mappers/royal_mail.py` | 64% | 32, 55, 59, 63 | ⚠️ Needs work |

## Critical Gaps

### 1. `src/formatter.py` - 0% Coverage ❌

**Issue:** CLI entry point has no tests.

**Missing:**
- CLI argument parsing
- Output path determination
- Error handling
- Success output formatting
- Verbose logging

**Recommendation:**
```python
# tests/integration/test_formatter_cli.py
def test_cli_basic_usage()
def test_cli_custom_output_path()
def test_cli_verbose_mode()
def test_cli_error_handling()
def test_cli_model_selection()
```

### 2. `src/core/validator.py` - 26% Coverage ❌

**Issue:** Core validation logic is barely tested.

**Missing:**
- `validate()` method (main entry point)
- Error handling for invalid schemas
- Nested validation logic
- Edge cases

**Recommendation:**
```python
# tests/unit/test_validator.py
def test_validate_success()
def test_validate_invalid_schema()
def test_validate_missing_required_fields()
def test_validate_invalid_endpoints()
def test_validate_error_messages()
```

### 3. `src/mappers/dpd_mapper.py` - 53% Coverage ⚠️

**Issue:** Many mapper methods untested.

**Missing:**
- `map_tracking_response()` complete flow
- Error handling for missing fields
- Edge cases (empty responses, null values)
- Date parsing edge cases
- Country derivation logic

**Recommendation:**
- Add tests for all mapper methods
- Test error handling paths
- Test edge cases

### 4. `src/llm_extractor.py` - 72% Coverage ⚠️

**Issue:** Error handling and edge cases not tested.

**Missing:**
- Error handling in `extract_schema()`
- JSON extraction edge cases
- Validation error handling
- Field mappings error handling
- Constraints error handling

**Current Issues:**
- 4 failing tests need fixing
- Mock setup issues in tests

## Failing Tests (Must Fix)

### 1. `test_extract_schema_success`
**Error:** `ValueError: Failed to extract schema from PDF text: the JSON object must be str, bytes or bytearray, not MagicMock`

**Fix:** Mock response.content properly, not the response object.

### 2. `test_extract_field_mappings`
**Error:** `KeyError: 'Input to ChatPromptTemplate is missing variables'`

**Fix:** Update prompt template to match actual variable names.

### 3. `test_extract_constraints`
**Error:** `assert 0 == 1` (empty list returned)

**Fix:** Mock should return proper JSON array.

### 4. `test_extract_text_with_tables_enabled`
**Error:** Assertion mismatch on table format

**Fix:** Update test expectation to match actual table format.

## Coverage Goals

| Priority | Module | Target | Current | Gap |
|----------|--------|--------|---------|-----|
| 🔴 Critical | `src/core/validator.py` | 90% | 26% | 64% |
| 🔴 Critical | `src/formatter.py` | 80% | 0% | 80% |
| 🟡 High | `src/mappers/dpd_mapper.py` | 85% | 53% | 32% |
| 🟡 High | `src/llm_extractor.py` | 85% | 72% | 13% |
| 🟢 Medium | `src/mappers/royal_mail.py` | 80% | 64% | 16% |

**Overall Target:** 85% coverage

## Recommendations

### Immediate Actions

1. **Fix failing tests** (4 tests)
   - Update mocks in `test_llm_extractor.py`
   - Fix prompt template variable names
   - Update table format expectations

2. **Add validator tests** (Critical)
   - Create `tests/unit/test_validator.py`
   - Test all validation paths
   - Test error handling

3. **Add CLI tests** (Critical)
   - Create `tests/integration/test_formatter_cli.py`
   - Test all CLI options
   - Test error handling

### Short-term Improvements

4. **Improve mapper coverage**
   - Add edge case tests for `dpd_mapper.py`
   - Test error handling paths
   - Test all transformation methods

5. **Improve LLM extractor coverage**
   - Add error handling tests
   - Test JSON extraction edge cases
   - Test validation failures

### Long-term Improvements

6. **Add integration tests**
   - End-to-end PDF → JSON flow
   - Real PDF processing (with mocks for LLM)
   - Error recovery scenarios

7. **Add performance tests**
   - Large PDF handling
   - Token limit handling
   - Timeout scenarios

## Test Organization

**Current Structure:**
```
tests/
├── unit/              # Fast, isolated tests
│   ├── test_schema.py
│   ├── test_validator.py (MISSING)
│   ├── test_mappers.py
│   └── test_llm_extractor.py
├── integration/       # Slower, full flow tests
│   ├── test_pipeline.py
│   └── test_formatter_cli.py (MISSING)
└── conftest.py       # Shared fixtures
```

**Good:** Well organized, follows Laravel pattern  
**Missing:** Validator tests, CLI tests

## Code Quality Issues Found

1. **Pydantic deprecation warnings**
   - `dict()` → `model_dump()` (Pydantic v2)
   - `config` class → `ConfigDict` (Pydantic v2)
   - `json_encoders` → custom serializers

2. **Missing error handling tests**
   - Many error paths untested
   - Edge cases not covered

3. **Mock setup issues**
   - LLM extractor tests have incorrect mocks
   - Need to fix response structure

## Next Steps

1. ✅ Fix 4 failing tests
2. ✅ Add `test_validator.py` (critical)
3. ✅ Add `test_formatter_cli.py` (critical)
4. ✅ Improve mapper test coverage
5. ✅ Fix Pydantic deprecation warnings
6. ✅ Add error handling tests

**Estimated effort:** 4-6 hours to reach 85% coverage
