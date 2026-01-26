# Table Detection and Marking

## How Tables Are Detected

The PDF parser uses `pdfplumber`'s `extract_tables()` method, which detects tables using heuristics:

1. **Cell Alignment** - Detects rows/columns of aligned text
2. **Borders** - Identifies visible table borders/lines
3. **Spacing** - Recognizes consistent spacing patterns
4. **Structure** - Identifies grid-like patterns

## How Tables Are Marked in Output

Currently, tables are marked with a simple prefix:

```
[Table on page 5]
Parameter Name | Type | Required | Description
tracking_number | string | Yes | DHL tracking number
format | string | No | Response format
```

## Problem: Hard to Identify Tables in Plain Text

When the extracted text is sent to an LLM, it's hard to distinguish:
- Regular text paragraphs
- Table data (which should be parsed as structured data)
- Lists vs tables

## Better Approach: Structured Output Format

We could improve this by:

### Option 1: JSON Output with Table Metadata

```json
{
  "text": "...regular text...",
  "tables": [
    {
      "page": 5,
      "type": "parameter_table",
      "data": [
        ["Parameter Name", "Type", "Required", "Description"],
        ["tracking_number", "string", "Yes", "DHL tracking number"]
      ],
      "headers": ["Parameter Name", "Type", "Required", "Description"]
    }
  ]
}
```

### Option 2: Markdown Tables

Convert tables to Markdown format (easier for LLMs to parse):

```markdown
## Table on Page 5

| Parameter Name | Type | Required | Description |
|---------------|------|----------|-------------|
| tracking_number | string | Yes | DHL tracking number |
| format | string | No | Response format |
```

### Option 3: Enhanced Text Markers

Use clearer markers and metadata:

```
=== TABLE START: Parameter Table (Page 5) ===
HEADERS: Parameter Name | Type | Required | Description
DATA:
tracking_number | string | Yes | DHL tracking number
format | string | No | Response format
=== TABLE END ===
```

## Recommendation

For LLM processing, **Option 2 (Markdown tables)** is best because:
- LLMs understand Markdown tables well
- Easy to parse programmatically
- Preserves structure clearly
- Standard format
