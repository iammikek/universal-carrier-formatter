"""
Mappers package initialization.
"""

from .dpd_mapper import DpdMapper
from .example_royal_mail import ExampleRoyalMailMapper

# Dynamically import generated mappers if they exist
try:
    from .dhl_express_mapper import DhlExpressMapper

    __all__ = ["DpdMapper", "ExampleRoyalMailMapper", "DhlExpressMapper"]
except ImportError:
    __all__ = ["DpdMapper", "ExampleRoyalMailMapper"]
