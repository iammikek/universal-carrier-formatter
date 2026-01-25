"""
Example Service Class Template

This file demonstrates how we'll structure service classes with Laravel comparisons.
This is a template - actual implementations will follow this pattern.
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Set up logging (like Laravel's Log facade)
# In Laravel: use Illuminate\Support\Facades\Log;
logger = logging.getLogger(__name__)


class ExampleService:
    """
    Example Service Class
    
    Laravel Equivalent: app/Services/ExampleService.php
    
    class ExampleService
    {
        public function __construct(
            private Config $config
        ) {}
        
        public function process(string $input): array
        {
            // Implementation
        }
    }
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Constructor (like Laravel's __construct)
        
        Laravel Equivalent:
        public function __construct(
            private Config $config
        ) {}
        
        In Python:
        - No access modifiers (public/private) - use underscore prefix for private
        - Type hints use -> syntax: def method(self) -> str:
        - Optional[Type] means the parameter can be None
        """
        self.config = config or {}
        # Initialize dependencies here (like Laravel's dependency injection)
    
    def process(self, input_data: str) -> Dict[str, Any]:
        """
        Public method to process data
        
        Laravel Equivalent:
        public function process(string $inputData): array
        {
            Log::info("Processing data", ['input' => $inputData]);
            
            $result = $this->doWork($inputData);
            
            return $result;
        }
        
        Python differences:
        - Type hints: input_data: str means parameter is string
        - Return type: -> Dict[str, Any] means returns dictionary
        - No $ for variables
        """
        logger.info(f"Processing data: {input_data}")
        
        # Call private method (like $this->doWork() in Laravel)
        result = self._do_work(input_data)
        
        return result
    
    def _do_work(self, data: str) -> Dict[str, Any]:
        """
        Private method (underscore prefix indicates private)
        
        Laravel Equivalent:
        private function doWork(string $data): array
        {
            // Implementation
        }
        
        Note: Python doesn't enforce privacy - underscore is a convention
        """
        # Implementation here
        return {"processed": data}
    
    @staticmethod
    def helper_method(value: str) -> str:
        """
        Static method (like Laravel's static methods)
        
        Laravel Equivalent:
        public static function helperMethod(string $value): string
        {
            return strtoupper($value);
        }
        
        Usage:
        - Laravel: ExampleService::helperMethod('test')
        - Python: ExampleService.helper_method('test')
        """
        return value.upper()


# Example usage (like using the service in a Laravel controller)
if __name__ == "__main__":
    # Create service instance (like dependency injection in Laravel)
    # In Laravel: $service = app(ExampleService::class);
    service = ExampleService(config={"api_key": "test"})
    
    # Use the service
    result = service.process("test data")
    print(result)
    
    # Use static method
    upper = ExampleService.helper_method("hello")
    print(upper)
