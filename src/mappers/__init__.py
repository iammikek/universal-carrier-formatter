"""
Mappers package – Registry / Plugin architecture for carrier mappers.

Import base and registry, then import mapper modules so they self-register.
New carriers: add one mapping file that inherits CarrierMapperBase (or
CarrierAbstract) and uses @register_carrier("slug"); no changes to core or API.
"""

from .base import CarrierAbstract, CarrierMapperBase

# Import mappers so they register with CarrierRegistry
from .example_mapper import ExampleMapper
from .example_template_mapper import ExampleTemplateMapper
from .registry import CarrierRegistry, register_carrier
from .royal_mail_mapper import RoyalMailRestApiMapper

# Generated mappers (e.g. from mapper_generator_cli) inherit CarrierMapperBase and
# use @register_carrier("slug"), so they self-register when imported. Add an
# import for each generated mapper module here so it registers.
try:
    from .dhl_express_mapper import DhlExpressMapper  # noqa: F401
except ImportError:
    DhlExpressMapper = None  # type: ignore[misc, assignment]

__all__ = [
    "CarrierAbstract",
    "CarrierMapperBase",
    "CarrierRegistry",
    "register_carrier",
    "ExampleMapper",
    "ExampleTemplateMapper",
    "RoyalMailRestApiMapper",
    "DhlExpressMapper",
]
