"""
Models package initialization.

Laravel Equivalent: app/Models/ directory

This package contains all data models for the Universal Carrier Format.
"""

from .carrier_schema import (
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
]
