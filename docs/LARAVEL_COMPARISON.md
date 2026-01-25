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
├── formatter.py          # Like app/Http/Controllers/FormatterController.php
├── pdf_parser.py         # Like app/Services/PdfParserService.php
├── llm_extractor.py      # Like app/Services/LlmExtractorService.php
├── schema_mapper.py      # Like app/Services/SchemaMapperService.php
└── models/               # Like app/Models/
    └── carrier_schema.py # Like app/Models/CarrierSchema.php
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
    
    def parse(self, pdf_path):
        # Implementation
        pass

# Usage (manual DI or use dependency injection library)
from src.pdf_parser import PdfParserService

parser = PdfParserService(config={'api_key': '...'})
result = parser.parse('file.pdf')
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
# src/models/carrier_schema.py
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List

class Endpoint(BaseModel):
    path: str = Field(..., description="API endpoint path")
    method: str = Field(..., regex="^(GET|POST|PUT|DELETE)$")
    parameters: List[dict] = []

class CarrierSchema(BaseModel):
    name: str = Field(..., min_length=1)
    base_url: HttpUrl  # Automatically validates URL
    endpoints: List[Endpoint] = Field(..., min_items=1)
    
    @validator('name')
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
from src.pdf_parser import PdfParserService
from src.llm_extractor import LlmExtractorService

@click.command()
@click.option('--input', '-i', required=True, help='Input PDF file')
@click.option('--output', '-o', required=True, help='Output JSON file')
def format_carrier(input, output):
    """
    Format carrier PDF to Universal Carrier Format.
    Like: php artisan carrier:format input.pdf output.json
    """
    # Initialize services (like dependency injection)
    parser = PdfParserService()
    extractor = LlmExtractorService()
    
    # Process (like controller method)
    text = parser.extract(input)
    schema = extractor.extract(text)
    
    # Save output
    with open(output, 'w') as f:
        json.dump(schema.dict(), f, indent=2)
    
    click.echo(f"✅ Formatted carrier schema saved to {output}")

if __name__ == '__main__':
    format_carrier()
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
from typing import Optional

logger = logging.getLogger(__name__)

class PdfParserService:
    """
    PDF parsing service.
    Like: app/Services/PdfParserService.php in Laravel
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Constructor (like __construct in Laravel)
        """
        self.config = config or {}
        # Initialize PDF library here
    
    def extract(self, pdf_path: str) -> str:
        """
        Extract text from PDF.
        Like: public function extract(string $pdfPath): string
        """
        path = Path(pdf_path)
        
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Extract text
        text = self._parse_pdf(str(path))
        
        logger.info(f"Extracted text from PDF: {pdf_path}")
        
        return text
    
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
# tests/test_pdf_parser.py
import pytest
from src.pdf_parser import PdfParserService
from pathlib import Path

class TestPdfParser:
    """Test class (like Laravel test class)"""
    
    def test_extracts_text_from_pdf(self):
        """Test method (like Laravel test method)"""
        # Arrange
        pdf_path = Path('tests/fixtures/sample.pdf')
        service = PdfParserService()
        
        # Act
        result = service.extract(str(pdf_path))
        
        # Assert
        assert result is not None
        assert len(result) > 0
        assert 'API' in result
    
    def test_throws_exception_for_missing_file(self):
        """Test exception (like expectException in Laravel)"""
        service = PdfParserService()
        
        with pytest.raises(FileNotFoundError):
            service.extract('nonexistent.pdf')
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

@click.command()
@click.argument('input', type=click.Path(exists=True))
@click.option('--output', '-o', default='output.json', help='Output file')
def format_carrier(input, output):
    """
    Format carrier PDF.
    Like: php artisan carrier:format input.pdf --output=output.json
    """
    click.echo(f"Processing {input}...")
    
    # Process...
    
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
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Initialize LLM (like setting up HTTP client)
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0,
    api_key=os.getenv('OPENAI_API_KEY')
)

# Create prompt template (like preparing request data)
prompt = ChatPromptTemplate.from_template(
    "Extract API endpoints from: {document}"
)

# Chain them together (like method chaining)
chain = prompt | llm  # Pipe operator chains operations

# Execute (like sending HTTP request)
response = chain.invoke({"document": pdf_text})
```

**LangChain Chains** are like Laravel's Pipeline pattern:
- Each step transforms data
- Can chain multiple operations
- Easy to test individual steps

---

## Common Patterns Summary

| Laravel Pattern | Python/LangChain Equivalent |
|----------------|----------------------------|
| `Service::class` | `Service()` (instantiate class) |
| `$this->method()` | `self.method()` or `instance.method()` |
| `config('key')` | `Config.KEY` or `os.getenv('KEY')` |
| `Log::info()` | `logger.info()` |
| `Storage::disk()` | `Path()` or `open()` |
| `Validator::make()` | Pydantic models |
| `Http::post()` | `requests.post()` or LangChain |
| `Artisan::call()` | Click commands or `subprocess.run()` |
| `Cache::remember()` | `functools.lru_cache()` or Redis client |
| `DB::transaction()` | Context manager: `with transaction():` |

---

## Next Steps

As we build the project, each file will include comments explaining:
- What Laravel pattern it replaces
- How it's similar/different
- Why we chose this approach

This will help you understand Python patterns through familiar Laravel concepts!
