# Cheapest Model for PDF Extraction

## Answer: `gpt-4.1-nano` - $0.20 per million input tokens

## Cost Breakdown

For a typical PDF extraction (1M characters ≈ 268K tokens input, 10K tokens output):

| Model | Input Cost | Output Cost | **Total** | Savings vs Default |
|-------|------------|-------------|-----------|-------------------|
| **gpt-4.1-nano** | $0.0536 | $0.0080 | **$0.062** | **75% cheaper** ✅ |
| gpt-5-mini | $0.0670 | $0.0200 | $0.087 | 65% cheaper |
| gpt-4.1-mini (default) | $0.2143 | $0.0320 | $0.246 | Baseline |
| gpt-5.2 | $0.4687 | $0.1400 | $0.609 | 2.5x more expensive |

## How to Use the Cheapest Model

```bash
# Use gpt-4.1-nano for maximum cost savings
python -m src.formatter examples/dhl_express_api_docs.pdf \
  --llm-model gpt-4.1-nano \
  --output output/dhl_schema.json
```

Or in code:
```python
from src.extraction_pipeline import ExtractionPipeline

pipeline = ExtractionPipeline(llm_model="gpt-4.1-nano")
schema = pipeline.process("examples/dhl_express_api_docs.pdf")
```

## Trade-offs

**gpt-4.1-nano advantages:**
- ✅ **Cheapest** - 75% cost reduction vs default
- ✅ Still under $2.5/1M token constraint
- ✅ Good for simple, well-structured PDFs

**gpt-4.1-nano considerations:**
- ⚠️ May have lower accuracy for complex schemas
- ⚠️ Smaller context window (check limits)
- ⚠️ May miss edge cases or nuanced details

**Recommendation:**
- **Start with `gpt-4.1-nano`** for cost savings
- **Validate the output** - check if schema is complete/accurate
- **Upgrade to `gpt-4.1-mini`** if quality is insufficient

## Real-World Cost Impact

**Processing 100 carrier PDFs:**

| Model | Total Cost |
|-------|------------|
| gpt-4.1-nano | **~$6.20** |
| gpt-4.1-mini (default) | ~$24.60 |
| gpt-5.2 | ~$60.90 |

**Savings with nano: ~$18.40 per 100 PDFs**

## Why We Extract Text First

Since we're using `pdfplumber` to extract text from PDFs **before** sending to LLM:

1. **PDF → Text** (free, local processing)
2. **Text → LLM** (cost: tokens)

The LLM only processes the **text**, not the raw PDF. This means:
- We pay for tokens, not PDF size
- Text extraction is free (local library)
- Cost is purely based on text length sent to LLM

## Cost Optimization Tips

1. **Use `gpt-4.1-nano`** for maximum savings
2. **Pre-process PDFs** - remove unnecessary pages/sections
3. **Split large PDFs** - process sections separately if needed
4. **Cache results** - don't re-process the same PDF
5. **Validate quality** - ensure nano model accuracy is acceptable

## Testing Quality

After switching to `gpt-4.1-nano`, validate:
- ✅ All endpoints extracted
- ✅ Request/response schemas complete
- ✅ Field mappings accurate
- ✅ Constraints captured

If quality is insufficient, consider:
- `gpt-5-mini` ($0.25/1M) - middle ground
- `gpt-4.1-mini` ($0.80/1M) - default, best quality
