"""
Mappers package initialization.
"""

from .example_mapper import ExampleMapper
from .example_template_mapper import ExampleTemplateMapper

# Dynamically import generated mappers if they exist
try:
    from .dhl_express_mapper import DhlExpressMapper

    __all__ = ["ExampleMapper", "ExampleTemplateMapper", "DhlExpressMapper"]
except ImportError:
    __all__ = ["ExampleMapper", "ExampleTemplateMapper"]
