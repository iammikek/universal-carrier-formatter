"""
Core package initialization.

Laravel Equivalent: app/Core/ directory

This package contains the universal schema and validation logic.
All carrier-specific implementations map to this core schema.
"""

from .schema import (AuthenticationMethod, Endpoint, HttpMethod, Parameter,
                     ParameterLocation, ParameterType, RateLimit,
                     RequestSchema, ResponseSchema, UniversalCarrierFormat,
                     UniversalFieldNames)

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
]
