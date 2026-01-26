"""
Mappers package initialization.
"""

from .example_mapper import ExampleMapper
from .example_royal_mail import ExampleRoyalMailMapper

# Dynamically import generated mappers if they exist
try:
    from .dhl_express_mapper import DhlExpressMapper

    __all__ = ["ExampleMapper", "ExampleRoyalMailMapper", "DhlExpressMapper"]
except ImportError:
    __all__ = ["ExampleMapper", "ExampleRoyalMailMapper"]
