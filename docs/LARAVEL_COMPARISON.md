# Laravel → Python/LangChain Comparison Guide

This guide explains Python/LangChain concepts by comparing them to Laravel patterns you already know.

## Table of Contents
1. [Project Structure](#project-structure)
2. [Dependency Management](#dependency-management)
3. [Service Providers & Dependency Injection](#service-providers--dependency-injection)
4. [Models & Data Validation](#models--data-validation)
5. [Controllers & Routes](#controllers--routes)
6. [Service Classes](#service-classes)
7. [Configuration](#configuration)
8. [Error Handling](#error-handling)
9. [Testing](#testing)
10. [CLI Commands](#cli-commands)

---

## Project Structure

### Laravel Structure
```
app/
├── Http/
│   ├── Controllers/
│   └── Middleware/
├── Models/
├── Services/
├── Providers/
└── Console/
config/
routes/
tests/
```

### Python Equivalent
```
src/
├── formatter.py              # Like app/Console/Commands/FormatCarrier.php
├── pdf_parser.py             # Like app/Services/PdfParserService.php
├── llm_extractor.py          # Like app/Services/LlmExtractorService.php
├── extraction_pipeline.py    # Like app/Services/ExtractionPipelineService.php
├── mapper_generator.py        # Like app/Services/MapperGeneratorService.php
├── mapper_generator_cli.py    # Like app/Console/Commands/GenerateMapper.php
├── core/                      # Like app/Models/ (core data models)
│   ├── schema.py              # Like app/Models/CarrierSchema.php
│   └── validator.py           # Like app/Services/CarrierValidator.php
├── mappers/                   # Like app/Services/Mappers/
│   ├── example_mapper.py      # Like app/Services/Mappers/ExampleMapper.php
│   └── example_template_mapper.py
└── blueprints/                # Like config/carriers/ (configuration)
    ├── loader.py              # Like app/Services/BlueprintLoader.php
    ├── validator.py           # Like app/Services/BlueprintValidator.php
    ├── converter.py           # Like app/Services/BlueprintConverter.php
    ├── processor.py          # Like app/Services/BlueprintProcessor.php
    └── cli.py                 # Like app/Console/Commands/ProcessBlueprint.php
```

**Key Difference**: Python uses modules (files) instead of classes in separate files. One file can contain multiple classes/functions.

---

## Dependency Management

### Laravel (Composer)
```php
// composer.json
{
    "require": {
        "guzzlehttp/guzzle": "^7.0"
    }
}

// Install
composer install
```

### Python (pip)
```python
# requirements.txt
requests>=2.31.0

# Install
pip install -r requirements.txt
```

**Similarity**: Both use dependency files and lock versions. Python's `requirements.txt` is like `composer.json` + `composer.lock`.

---

## Service Providers & Dependency Injection

### Laravel Service Provider
```php
// app/Providers/AppServiceProvider.php
public function register()
{
    $this->app->singleton(PdfParserService::class, function ($app) {
        return new PdfParserService();
    });
}

// Usage in Controller
public function __construct(PdfParserService $parser)
{
    $this->parser = $parser;
}
```

### Python Equivalent
```python
# src/pdf_parser.py
class PdfParserService:
    def __init__(self, config=None):
        self.config = config or {}
    
    def extract_text(self, pdf_path):
        # Implementation
        pass

# Usage (manual DI or use dependency injection library)
from src.pdf_parser import PdfParserService

parser = PdfParserService(config={'extract_tables': True})
result = parser.extract_text('file.pdf')
```

**Note**: Python doesn't have built-in DI container like Laravel, but you can:
- Use manual dependency injection
- Use libraries like `dependency-injector` (like Laravel's container)
- Use simple factory functions

---

## Models & Data Validation

### Laravel Model with Validation
```php
// app/Models/CarrierSchema.php
class CarrierSchema extends Model
{
    protected $fillable = ['name', 'base_url', 'endpoints'];
    
    public static function validate(array $data)
    {
        return Validator::make($data, [
            'name' => 'required|string',
            'base_url' => 'required|url',
            'endpoints' => 'required|array',
        ]);
    }
}
```

### Python with Pydantic (Like Laravel Models)
```python
# src/core/schema.py
from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import List

class Endpoint(BaseModel):
    path: str = Field(..., description="API endpoint path")
    method: str = Field(..., pattern="^(GET|POST|PUT|DELETE)$")
    parameters: List[dict] = []

class UniversalCarrierFormat(BaseModel):
    name: str = Field(..., min_length=1)
    base_url: HttpUrl  # Automatically validates URL
    endpoints: List[Endpoint] = Field(..., min_length=1)
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Example Carrier",
                "base_url": "https://api.example.com",
                "endpoints": []
            }
        }
```

**Pydantic Benefits** (like Laravel validation):
- Automatic validation on instantiation
- Type hints (like PHP type hints)
- JSON schema generation
- Clear error messages

---

## Controllers & Routes

### Laravel Controller
```php
// app/Http/Controllers/FormatterController.php
class FormatterController extends Controller
{
    public function __construct(
        private PdfParserService $parser,
        private LlmExtractorService $extractor
    ) {}
    
    public function format(Request $request)
    {
        $validated = $request->validate([
            'pdf' => 'required|file|mimes:pdf',
        ]);
        
        $pdfPath = $validated['pdf']->store('temp');
        $text = $this->parser->extract($pdfPath);
        $schema = $this->extractor->extract($text);
        
        return response()->json($schema);
    }
}

// routes/api.php
Route::post('/format', [FormatterController::class, 'format']);
```

### Python CLI (Like Artisan Command)
```python
# src/formatter.py
import click
from src.extraction_pipeline import ExtractionPipeline

@click.command()
@click.argument('input', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output JSON file')
@click.option('--llm-model', default='gpt-4.1-mini', help='LLM model to use')
def main(input, output):
    """
    Format carrier PDF to Universal Carrier Format.
    Like: php artisan carrier:format input.pdf --output=output.json
    """
    # Initialize pipeline (like dependency injection)
    pipeline = ExtractionPipeline(llm_model='gpt-4.1-mini')
    
    # Process (like controller method)
    schema = pipeline.process(input, output)
    
    click.echo(f"✅ Formatted carrier schema saved to {output}")

if __name__ == '__main__':
    main()
```

**Click** is like Laravel's Artisan commands - handles CLI argument parsing and validation.

---

## Service Classes

### Laravel Service
```php
// app/Services/PdfParserService.php
class PdfParserService
{
    public function __construct(
        private Config $config
    ) {}
    
    public function extract(string $pdfPath): string
    {
        if (!file_exists($pdfPath)) {
            throw new FileNotFoundException("PDF not found: {$pdfPath}");
        }
        
        // Extract text using library
        $text = $this->parsePdf($pdfPath);
        
        Log::info("Extracted text from PDF", ['path' => $pdfPath]);
        
        return $text;
    }
    
    private function parsePdf(string $path): string
    {
        // Implementation
    }
}
```

### Python Service Class
```python
# src/pdf_parser.py
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class PdfParserService:
    """
    PDF parsing service.
    Like: app/Services/PdfParserService.php in Laravel
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Constructor (like __construct in Laravel)
        """
        self.config = config or {}
        # Initialize PDF library here
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF.
        Like: public function extractText(string $pdfPath): string
        """
        path = Path(pdf_path)
        
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Extract text
        text = self._parse_pdf(str(path))
        
        logger.info(f"Extracted text from PDF: {pdf_path}")
        
        return text
    
    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF.
        Like: public function extractMetadata(string $pdfPath): array
        """
        # Implementation
        pass
    
    def _parse_pdf(self, path: str) -> str:
        """
        Private method (like private function in Laravel).
        Underscore prefix indicates private.
        """
        # Implementation
        pass
```

**Key Differences**:
- Python uses `_method_name` for private methods (convention, not enforced)
- Type hints use `->` syntax: `def method(self) -> str:`
- No `$` for variables
- `Path` is like Laravel's `Storage` facade

---

## Configuration

### Laravel Config
```php
// config/services.php
return [
    'openai' => [
        'api_key' => env('OPENAI_API_KEY'),
        'model' => env('OPENAI_MODEL', 'gpt-4'),
    ],
];

// Usage
$apiKey = config('services.openai.api_key');
```

### Python Config
```python
# config.py or use python-dotenv
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file (like Laravel's env() helper)

class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Usage
from config import Config
api_key = Config.OPENAI_API_KEY
```

**Similarity**: Both use `.env` files and `env()` helper (Python: `os.getenv()`).

---

## Error Handling

### Laravel Exception Handling
```php
try {
    $result = $this->service->process($data);
} catch (FileNotFoundException $e) {
    Log::error("File not found", ['error' => $e->getMessage()]);
    return response()->json(['error' => 'File not found'], 404);
} catch (\Exception $e) {
    Log::error("Unexpected error", ['error' => $e->getMessage()]);
    return response()->json(['error' => 'Processing failed'], 500);
}
```

### Python Exception Handling
```python
import logging

logger = logging.getLogger(__name__)

try:
    result = service.process(data)
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    return {'error': 'File not found'}, 404
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {'error': 'Processing failed'}, 500
```

**Similarity**: Both use try/except (catch) blocks. Python's exceptions are classes like PHP.

---

## Testing

### Laravel Feature Test
```php
// tests/Feature/PdfParserTest.php
class PdfParserTest extends TestCase
{
    public function test_extracts_text_from_pdf()
    {
        // Arrange
        $pdfPath = base_path('tests/fixtures/sample.pdf');
        $service = new PdfParserService();
        
        // Act
        $result = $service->extract($pdfPath);
        
        // Assert
        $this->assertNotEmpty($result);
        $this->assertStringContainsString('API', $result);
    }
    
    public function test_throws_exception_for_missing_file()
    {
        $this->expectException(FileNotFoundException::class);
        
        $service = new PdfParserService();
        $service->extract('nonexistent.pdf');
    }
}
```

### Python Test (pytest)
```python
# tests/unit/test_pdf_parser.py
import pytest
from src.pdf_parser import PdfParserService
from pathlib import Path

@pytest.mark.unit
class TestPdfParserService:
    """Test class (like Laravel test class)"""
    
    def test_extracts_text_from_pdf(self):
        """Test method (like Laravel test method)"""
        # Arrange
        pdf_path = Path('tests/fixtures/sample.pdf')
        service = PdfParserService()
        
        # Act
        result = service.extract_text(str(pdf_path))
        
        # Assert
        assert result is not None
        assert len(result) > 0
        assert 'API' in result
    
    def test_throws_exception_for_missing_file(self):
        """Test exception (like expectException in Laravel)"""
        service = PdfParserService()
        
        with pytest.raises(FileNotFoundError):
            service.extract_text('nonexistent.pdf')
```

**pytest** is like PHPUnit:
- `assert` instead of `$this->assert*()`
- `pytest.raises()` instead of `expectException()`
- Fixtures instead of `setUp()` methods

---

## CLI Commands

### Laravel Artisan Command
```php
// app/Console/Commands/FormatCarrier.php
class FormatCarrier extends Command
{
    protected $signature = 'carrier:format 
                            {input : The input PDF file}
                            {--output= : Output JSON file}';
    
    public function handle()
    {
        $input = $this->argument('input');
        $output = $this->option('output') ?? 'output.json';
        
        $this->info("Processing {$input}...");
        
        // Process...
        
        $this->info("✅ Saved to {$output}");
    }
}
```

### Python Click Command
```python
# src/formatter.py
import click
from pathlib import Path
from src.extraction_pipeline import ExtractionPipeline

@click.command()
@click.argument('input', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), help='Output file')
@click.option('--llm-model', default='gpt-4.1-mini', help='LLM model to use')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed logs')
def main(input: Path, output: Path, llm_model: str, verbose: bool):
    """
    Format carrier PDF to Universal Carrier Format.
    Like: php artisan carrier:format input.pdf --output=output.json
    """
    click.echo(f"Processing {input}...")
    
    # Initialize pipeline
    pipeline = ExtractionPipeline(llm_model=llm_model)
    
    # Process
    schema = pipeline.process(str(input), str(output) if output else None)
    
    click.echo(f"✅ Saved to {output}")
```

**Click** decorators are like Laravel's command signature:
- `@click.argument()` = `{argument}`
- `@click.option()` = `{--option}`
- `click.echo()` = `$this->info()`

---

## LangChain Specific Patterns

### Laravel HTTP Client (Guzzle)
```php
$response = Http::withHeaders([
    'Authorization' => 'Bearer ' . $apiKey,
])->post('https://api.openai.com/v1/chat/completions', [
    'model' => 'gpt-4',
    'messages' => [['role' => 'user', 'content' => $prompt]],
]);
```

### LangChain LLM Call
```python
# src/llm_extractor.py
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import os

class LlmExtractorService:
    """
    LLM extraction service.
    Like: app/Services/LlmExtractorService.php in Laravel
    """
    
    def __init__(self, model: str = "gpt-4.1-mini", api_key: str = None):
        """
        Initialize LLM (like setting up HTTP client in constructor)
        """
        self.llm = ChatOpenAI(
            model=model,
            temperature=0,
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
    
    def extract_schema(self, pdf_text: str):
        """
        Extract schema from PDF text.
        Like: public function extractSchema(string $pdfText): CarrierSchema
        """
        # Create prompt template (like preparing request data)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert API documentation parser."),
            ("user", "Extract API endpoints from: {pdf_text}")
        ])
        
        # Chain them together (like method chaining)
        chain = prompt | self.llm  # Pipe operator chains operations
        
        # Execute (like sending HTTP request)
        response = chain.invoke({"pdf_text": pdf_text})
        
        return self._extract_json_from_response(response.content)
```

**LangChain Chains** are like Laravel's Pipeline pattern:
- Each step transforms data
- Can chain multiple operations
- Easy to test individual steps

---

## Common Patterns Summary

| Laravel Pattern | Python/LangChain Equivalent | Example File |
|----------------|----------------------------|--------------|
| `Service::class` | `Service()` (instantiate class) | `src/pdf_parser.py` |
| `$this->method()` | `self.method()` or `instance.method()` | All service classes |
| `config('key')` | `Config.KEY` or `os.getenv('KEY')` | `src/formatter.py` |
| `Log::info()` | `logger.info()` | All service classes |
| `Storage::disk()` | `Path()` or `open()` | `src/pdf_parser.py` |
| `Validator::make()` | Pydantic models | `src/core/validator.py` |
| `Http::post()` | `requests.post()` or LangChain | `src/llm_extractor.py` |
| `Artisan::call()` | Click commands | `src/formatter.py`, `src/blueprints/cli.py` |
| `Cache::remember()` | `functools.lru_cache()` or Redis client | (Not yet implemented) |
| `DB::transaction()` | Context manager: `with transaction():` | (Not yet implemented) |
| `Model::class` | Pydantic `BaseModel` | `src/core/schema.py` |
| `app/Models/` | `src/core/` | `src/core/schema.py` |
| `app/Services/` | `src/` (service files) | `src/pdf_parser.py`, `src/llm_extractor.py` |
| `app/Console/Commands/` | `src/*_cli.py` or `src/formatter.py` | `src/formatter.py`, `src/blueprints/cli.py` |
| `config/` | `blueprints/` (YAML configs) | `blueprints/dhl_express.yaml` |

---

## Current Project Structure Mapping

### Laravel → Python File Mapping

| Laravel Location | Python Location | Purpose |
|----------------|----------------|---------|
| `app/Console/Commands/FormatCarrier.php` | `src/formatter.py` | CLI entry point for PDF formatting |
| `app/Services/PdfParserService.php` | `src/pdf_parser.py` | PDF text extraction |
| `app/Services/LlmExtractorService.php` | `src/llm_extractor.py` | LLM-based schema extraction |
| `app/Services/ExtractionPipelineService.php` | `src/extraction_pipeline.py` | Orchestrates PDF → LLM → Validation |
| `app/Services/MapperGeneratorService.php` | `src/mapper_generator.py` | Generates mapper code from schemas |
| `app/Console/Commands/GenerateMapper.php` | `src/mapper_generator_cli.py` | CLI for mapper generation |
| `app/Models/CarrierSchema.php` | `src/core/schema.py` | Universal Carrier Format models |
| `app/Services/CarrierValidator.php` | `src/core/validator.py` | Schema validation |
| `app/Services/Mappers/ExampleMapper.php` | `src/mappers/example_mapper.py` | Example mapper implementation |
| `app/Services/BlueprintLoader.php` | `src/blueprints/loader.py` | Loads YAML blueprints |
| `app/Services/BlueprintValidator.php` | `src/blueprints/validator.py` | Validates blueprint structure |
| `app/Services/BlueprintConverter.php` | `src/blueprints/converter.py` | Converts blueprint to Universal Format |
| `app/Services/BlueprintProcessor.php` | `src/blueprints/processor.py` | Orchestrates blueprint processing |
| `app/Console/Commands/ProcessBlueprint.php` | `src/blueprints/cli.py` | CLI for blueprint processing |
| `config/carriers/dhl_express.php` | `blueprints/dhl_express.yaml` | Carrier configuration |

## Next Steps

As we build the project, each file includes comments explaining:
- What Laravel pattern it replaces
- How it's similar/different
- Why we chose this approach

This helps you understand Python patterns through familiar Laravel concepts!
