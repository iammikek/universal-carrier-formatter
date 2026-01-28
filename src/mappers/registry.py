"""
Carrier Registry – plugin-style lookup for carrier mappers.

Mappers register themselves by slug (e.g. "example", "dhl"). The core
and API use the registry to get a mapper by name instead of hardcoding.
"""

from typing import List, Type

from .base import CarrierMapperBase


class CarrierRegistry:
    """
    Registry of carrier mappers by slug.

    Use register() to add a mapper, get() to obtain an instance by slug.
    Contributing a new carrier = add a mapper class + one register() call
    (or @register_carrier("slug") on the class); no changes to core or API.
    """

    _mappers: dict[str, Type[CarrierMapperBase]] = {}

    @classmethod
    def register(cls, slug: str, mapper_class: Type[CarrierMapperBase]) -> None:
        """Register a mapper class under a slug (e.g. 'example', 'dhl')."""
        if not issubclass(mapper_class, CarrierMapperBase):
            raise TypeError(
                f"Mapper must be a subclass of CarrierMapperBase, got {mapper_class}"
            )
        cls._mappers[slug.lower().strip()] = mapper_class

    @classmethod
    def get(cls, slug: str) -> CarrierMapperBase:
        """
        Return a new mapper instance for the given slug.

        Raises:
            KeyError: If slug is not registered.
        """
        key = slug.lower().strip()
        if key not in cls._mappers:
            available = ", ".join(sorted(cls._mappers.keys())) or "(none)"
            raise KeyError(f"Unknown carrier: {slug!r}. Registered: {available}")
        return cls._mappers[key]()

    @classmethod
    def list_names(cls) -> List[str]:
        """Return sorted list of registered carrier slugs."""
        return sorted(cls._mappers.keys())

    @classmethod
    def is_registered(cls, slug: str) -> bool:
        """Return True if slug is registered."""
        return slug.lower().strip() in cls._mappers


def register_carrier(slug: str):
    """
    Decorator to register a mapper class under a slug.

    Usage:
        @register_carrier("example")
        class ExampleMapper(CarrierMapperBase):
            ...
    """

    def decorator(mapper_class: Type[CarrierMapperBase]) -> Type[CarrierMapperBase]:
        CarrierRegistry.register(slug, mapper_class)
        return mapper_class

    return decorator
