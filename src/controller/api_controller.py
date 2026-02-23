"""
API controller facade: composes domain controllers and exposes endpoint logic.

Routers depend on ApiController; it delegates to ExtractController, ConvertController,
and CarrierController so each domain stays in one place.
"""

from typing import Any, Dict, List

from .carriers import CarrierController
from .convert import ConvertController
from .extract import ExtractController


class ApiController:
    """Facade for Universal Carrier Formatter API endpoints. Delegates to domain controllers."""

    def __init__(
        self,
        extract_controller: ExtractController | None = None,
        convert_controller: ConvertController | None = None,
        carrier_controller: CarrierController | None = None,
    ):
        self._extract = extract_controller or ExtractController()
        self._convert = convert_controller or ConvertController()
        self._carriers = carrier_controller or CarrierController()

    def root(self) -> Dict[str, str]:
        """Service info and links to docs."""
        return {
            "service": "Universal Carrier Formatter API",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "carriers": "GET /carriers (list registered carrier slugs)",
            "extract": "POST /extract (PDF file or JSON with extracted_text; ?async=1 for async job)",
            "extract_jobs": "GET /extract/jobs/{job_id} (poll async extract result)",
            "convert": "POST /convert (carrier response → universal JSON)",
            "carrier_openapi": "GET /carriers/{name}/openapi.yaml (OpenAPI for a carrier schema)",
        }

    def health(self) -> Dict[str, str]:
        """Health check for load balancers and orchestration."""
        return {"status": "ok", "service": "universal-carrier-formatter"}

    def list_carriers(self) -> List[str]:
        """List carrier slugs available for conversion."""
        return self._carriers.list_carriers()

    def carrier_openapi_yaml(self, name: str) -> str:
        """Return OpenAPI YAML for the given carrier schema."""
        return self._carriers.carrier_openapi_yaml(name)

    async def extract(
        self,
        *,
        pdf_content: Any = None,
        extracted_text: Any = None,
        pdf_filename: Any = None,
        async_mode: bool = False,
    ):
        """Extract Universal Carrier Format from PDF or text. Delegates to ExtractController."""
        return await self._extract.extract(
            pdf_content=pdf_content,
            extracted_text=extracted_text,
            pdf_filename=pdf_filename,
            async_mode=async_mode,
        )

    def get_extract_job(self, job_id: str):
        """Get status or result of an async extract job. Delegates to ExtractController."""
        return self._extract.get_extract_job(job_id)

    def convert(self, carrier_response: Dict[str, Any], carrier: Any = None) -> Dict[str, Any]:
        """Convert carrier response to universal JSON. Delegates to ConvertController."""
        return self._convert.convert(carrier_response, carrier)
