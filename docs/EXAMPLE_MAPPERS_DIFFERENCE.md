# Difference Between Example Mappers

## Overview

We have two example mappers that serve different purposes:

1. **`example_mapper.py`** (ExampleMapper) - **Complete Reference Implementation**
2. **`example_template_mapper.py`** (ExampleTemplateMapper) - **Empty Template/Stub**

## Key Differences

| Aspect | `example_mapper.py` | `example_template_mapper.py` |
|--------|---------------------|------------------------------|
| **Purpose** | Complete working reference | Empty template/stub |
| **Size** | 274 lines | 69 lines |
| **Implementation** | Fully implemented | Empty methods (return `[]`) |
| **Test Coverage** | 96% | 64% (template file) |
| **Use Case** | Reference for mapper generator | Starting point for new mappers |

## `example_mapper.py` (ExampleMapper)

**What it has:**
- ✅ **Complete implementation** - All methods fully implemented
- ✅ **`map_tracking_response()`** - Transforms tracking responses (messy → universal)
- ✅ **`map_carrier_schema()`** - Transforms carrier schemas to UniversalCarrierFormat
- ✅ **Helper methods** - `_derive_country_from_postcode()`, date parsing, etc.
- ✅ **Field mappings** - `FIELD_MAPPING` and `STATUS_MAPPING` dictionaries
- ✅ **Full endpoint/auth/rate limit mapping** - All helper methods implemented

**Used for:**
- Reference pattern for the mapper generator (LLM uses this to generate new mappers)
- Complete example showing how mappers work
- Testing and demos

## `example_template_mapper.py` (ExampleTemplateMapper)

**What it has:**
- ⚠️ **Empty template** - Methods exist but return empty values
- ⚠️ **Only `map()` method** - Not `map_tracking_response()`
- ⚠️ **Empty helper methods** - `_map_endpoints()`, `_map_authentication()`, `_map_rate_limits()` all return `[]`
- ⚠️ **No field mappings** - No FIELD_MAPPING or STATUS_MAPPING

**Used for:**
- Starting point when creating a new mapper manually
- Shows the basic structure/interface
- Copy-paste template

## When to Use Which?

### Use `example_mapper.py` when:
- ✅ You want to see a **complete working example**
- ✅ You're using the **mapper generator** (it references this)
- ✅ You want to understand the **full pattern**
- ✅ You need a **reference for testing**

### Use `example_template_mapper.py` when:
- ✅ You're **manually creating** a new mapper
- ✅ You want a **minimal starting point**
- ✅ You prefer to **implement everything yourself**
- ✅ You want the **basic structure** without implementation

## Recommendation

**For most cases:** Use `example_mapper.py` as your reference. It's complete and shows everything you need.

**For manual creation:** Copy `example_template_mapper.py` if you prefer starting from scratch, but you'll need to implement everything yourself.

## Summary

- **`example_mapper.py`** = "Here's a complete, working mapper - use this as reference"
- **`example_template_mapper.py`** = "Here's an empty template - fill it in yourself"

The mapper generator uses `example_mapper.py` as its reference pattern, which is why it's fully implemented.
