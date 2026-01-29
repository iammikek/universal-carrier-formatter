"""
Core package initialization.

Contains the universal schema, validation logic, and canonical physical units.
All carrier-specific implementations map to this core schema.
"""

from .schema import (
    AuthenticationMethod,
    Endpoint,
    HttpMethod,
    Parameter,
    ParameterLocation,
    ParameterType,
    RateLimit,
    RequestSchema,
    ResponseSchema,
    UniversalCarrierFormat,
    UniversalFieldNames,
)
from .units import (
    LengthCm,
    WeightGrams,
    parse_length_to_cm,
    parse_weight_to_grams,
)

__all__ = [
    "UniversalCarrierFormat",
    "Endpoint",
    "Parameter",
    "RequestSchema",
    "ResponseSchema",
    "AuthenticationMethod",
    "RateLimit",
    "HttpMethod",
    "ParameterType",
    "ParameterLocation",
    "UniversalFieldNames",
    "WeightGrams",
    "LengthCm",
    "parse_weight_to_grams",
    "parse_length_to_cm",
]
