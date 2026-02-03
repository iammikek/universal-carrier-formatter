# Understanding "Per Extraction" Costs

## What is "Per Extraction"?

**"Per extraction"** means **each time you run the extraction pipeline on a single PDF file**.

One extraction = Processing one PDF file through the complete pipeline:
1. Extract text from PDF
2. Save extracted text (always; default: `output/<pdf_stem>_extracted_text.txt`)
3. Send text to LLM
4. Get JSON schema back
5. Validate and save

## Cost Breakdown

### Token-Based Pricing

OpenAI charges based on **tokens**, not characters. Here's how it works:

**Token conversion:**
- Roughly **1 token ≈ 4 characters** (for English text)
- So 1 million characters ≈ **250,000 tokens**

### Example: DHL Express PDF

From your actual run:
- **PDF size**: 1,071,343 characters extracted
- **Token estimate**: ~268,000 input tokens (1,071,343 ÷ 4)
- **Pages**: 485 pages

### Cost Calculation

**Input tokens** (PDF text sent to LLM):
- 268,000 tokens × $0.80 per 1M tokens = **$0.214**

**Output tokens** (JSON response from LLM):
- Estimated ~5,000-10,000 tokens for the schema
- 10,000 tokens × $3.20 per 1M tokens = **$0.032**

**Total per extraction**: ~**$0.25** for the DHL PDF

### Why This Matters

**"Per extraction"** means:
- Process 1 PDF = 1 extraction = ~$0.25 (for DHL-sized PDF)
- Process 10 PDFs = 10 extractions = ~$2.50
- Process 100 PDFs = 100 extractions = ~$25.00

### Cost Comparison

**Old default (gpt-4 at $3.00/1M input tokens):**
- Input: 268K tokens × $3.00 = **$0.804**
- Output: 10K tokens × $6.00 = **$0.060**
- **Total: ~$0.86 per extraction**

**New default (gpt-4.1-mini at $0.80/1M input tokens):**
- Input: 268K tokens × $0.80 = **$0.214**
- Output: 10K tokens × $3.20 = **$0.032**
- **Total: ~$0.25 per extraction**

**Savings: ~71% reduction** ($0.86 → $0.25)

## Real-World Usage

If you're onboarding carriers:
- **10 carriers/month**: ~$2.50/month
- **50 carriers/month**: ~$12.50/month
- **100 carriers/month**: ~$25.00/month

This is why the $2.5/1M token constraint matters - it keeps costs reasonable at scale.

## Token Limits

**Important**: Most models have token limits:
- `gpt-4.1-mini`: 128K tokens context window
- Your DHL PDF: ~268K tokens

**Solution**: For very large PDFs, you may need to:
1. Split the PDF into chunks
2. Process each chunk separately
3. Combine results

This would be multiple extractions, so multiple costs.
