# Adding a New Carrier (Plugin Architecture)

Every carrier plugs in as **one mapping file**: inherit the base class and register. 
## Architecture

- **CarrierAbstract / CarrierMapperBase** – Abstract base class. Every carrier mapper inherits from it and implements `map_tracking_response(carrier_response) -> dict` (universal format).
- **CarrierRegistry** – Central registry of mappers by slug. The API and core use `CarrierRegistry.get("slug")` and `CarrierRegistry.list_names()`; no hardcoded carrier logic.
- **@register_carrier("slug")** – Decorator so a mapper class registers itself under a slug (e.g. `"dhl"`, `"royal_mail"`). One decorator per class; no manual `register()` calls in core.

## Steps to Add a New Carrier (e.g. DPD)

1. **Create one mapping file** under `src/mappers/`, e.g. `src/mappers/dpd_mapper.py`.

2. **Inherit from the base and implement the required method:**

   ```python
   from ..core import UniversalFieldNames
   from .base import CarrierMapperBase  # or CarrierAbstract
   from .registry import register_carrier

   @register_carrier("dpd")
   class DpdMapper(CarrierMapperBase):
       FIELD_MAPPING = {
           "parcelId": UniversalFieldNames.TRACKING_NUMBER,
           "status": UniversalFieldNames.STATUS,
           # ...
       }
       STATUS_MAPPING = {"IN_TRANSIT": "in_transit", ...}

       def map_tracking_response(self, carrier_response):
           # Transform carrier response -> universal dict
           ...
           return universal_dict
   ```

3. **Register the module** so the registry sees it: in `src/mappers/__init__.py`, add:

   ```python
   from .dpd_mapper import DpdMapper  # noqa: F401
   ```

   and add `"DpdMapper"` to `__all__` if you want it exported.

4. **Done.** No changes to `api.py`, `registry.py`, or core logic. The API already uses `CarrierRegistry.get(req.carrier)` and `CarrierRegistry.list_names()`; your new slug (`"dpd"`) is available for `POST /convert` and `GET /carriers`.

## Conventions

- **Slug**: lowercase, snake_case (e.g. `dhl_express`, `royal_mail`). Used in `POST /convert` as `carrier` and in `GET /carriers`.
- **One file per carrier**: keeps the codebase uniform and makes it easy for others to add DHL, DPD, FedEx, etc. without touching the core.
- **Optional**: `map_carrier_schema` if the carrier has schema/docs you want to map to `UniversalCarrierFormat`; otherwise the base raises `NotImplementedError`.

## Generated mappers

The mapper generator (`python -m src.mapper_generator_cli schema.json -o src/mappers/foo_mapper.py`) produces a class that already inherits from `CarrierMapperBase` and uses `@register_carrier("slug")`. Add an import for that module in `src/mappers/__init__.py` (and optionally a try/except if the file is optional) so it self-registers when the package loads.

## Summary

| Goal                         | How we achieve it                                      |
|-----------------------------|--------------------------------------------------------|
| No hardcoded carrier logic  | API and core use `CarrierRegistry.get(slug)` only      |
| One mapping file per carrier | New carrier = new file + one import in `mappers/__init__.py` |
| Contributors don’t break core | All carriers inherit `CarrierMapperBase` and register; core never branches on carrier name |
