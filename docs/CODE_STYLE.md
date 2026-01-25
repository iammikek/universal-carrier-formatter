# Code Style Guide - Laravel Comparisons

## Comment Style for Laravel Comparisons

When writing code, include comments comparing to Laravel patterns:

```python
class MyService:
    """
    Service class description.
    
    Laravel Equivalent: app/Services/MyService.php
    
    class MyService
    {
        public function __construct(
            private Config $config
        ) {}
    }
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Constructor.
        
        Laravel Equivalent:
        public function __construct(
            private Config $config
        ) {}
        """
        self.config = config or {}
    
    def public_method(self, param: str) -> dict:
        """
        Public method description.
        
        Laravel Equivalent:
        public function publicMethod(string $param): array
        {
            // Implementation
        }
        """
        pass
    
    def _private_method(self):
        """
        Private method (underscore prefix).
        
        Laravel Equivalent:
        private function privateMethod()
        {
            // Implementation
        }
        """
        pass
```

## Key Patterns to Explain

1. **Service Classes**: Compare to Laravel services
2. **Dependency Injection**: Show manual DI vs Laravel's container
3. **Type Hints**: Compare Python type hints to PHP type hints
4. **Error Handling**: Compare try/except to try/catch
5. **Logging**: Compare Python logging to Laravel Log facade
6. **Configuration**: Compare os.getenv() to config() helper
7. **Testing**: Compare pytest to PHPUnit
8. **CLI**: Compare Click to Artisan commands

## When to Add Comparisons

- ✅ New service classes
- ✅ Complex methods that have Laravel equivalents
- ✅ Configuration patterns
- ✅ Error handling patterns
- ✅ Testing patterns
- ❌ Simple one-liners (unless they're conceptually important)
- ❌ Standard library functions (unless used in a Laravel-like pattern)

## Example: Full Service with Comparisons

See `src/_example_service_template.py` for a complete example.
