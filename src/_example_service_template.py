"""
Example Service Class Template.

Template for structuring service classes. Actual implementations follow this pattern.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ExampleService:
    """
    Example Service Class.

    Template for a service that processes input and returns structured data.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the service.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}

    def process(self, input_data: str) -> Dict[str, Any]:
        """
        Process input data.

        Args:
            input_data: Input string to process.

        Returns:
            Dictionary with processed result.
        """
        logger.info(f"Processing data: {input_data}")
        result = self._do_work(input_data)
        return result

    def _do_work(self, data: str) -> Dict[str, Any]:
        """
        Internal implementation (underscore prefix indicates internal use).

        Note: Python doesn't enforce privacy - underscore is a convention.
        """
        return {"processed": data}

    @staticmethod
    def helper_method(value: str) -> str:
        """
        Static helper method.

        Usage: ExampleService.helper_method('test')
        """
        return value.upper()


if __name__ == "__main__":
    service = ExampleService(config={"api_key": "test"})

    # Use the service
    result = service.process("test data")
    print(result)

    # Use static method
    upper = ExampleService.helper_method("hello")
    print(upper)
