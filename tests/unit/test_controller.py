"""
Unit tests for the API controller.

Validates ApiController endpoint logic in isolation with mocks for
CarrierRegistry, extract job store, and file I/O where needed.
"""

import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from src.controller import ApiController, _extract_jobs


@pytest.mark.unit
class TestApiController:
    """Test ApiController endpoint methods."""

    def test_root_returns_service_info(self):
        """root() returns dict with service name and doc links."""
        controller = ApiController()
        result = controller.root()
        assert result["service"] == "Universal Carrier Formatter API"
        assert result["docs"] == "/docs"
        assert result["openapi"] == "/openapi.json"
        assert "carriers" in result
        assert "extract" in result
        assert "convert" in result
        assert "carrier_openapi" in result

    def test_health_returns_ok(self):
        """health() returns status ok and service name."""
        controller = ApiController()
        result = controller.health()
        assert result["status"] == "ok"
        assert "universal-carrier-formatter" in result["service"]

    def test_list_carriers_returns_registry_names(self):
        """list_carriers() returns list of carrier slugs from registry."""
        controller = ApiController()
        with patch("src.controller.carriers.CarrierRegistry") as reg:
            reg.list_names.return_value = ["example", "dhl"]
            result = controller.list_carriers()
        assert result == ["example", "dhl"]

    def test_convert_success_returns_universal_json(self):
        """convert() uses mapper and returns universal format dict."""
        controller = ApiController()
        mock_mapper = MagicMock()
        mock_mapper.map_tracking_response.return_value = {
            "tracking_number": "123",
            "status": "delivered",
        }
        with patch("src.controller.convert.CarrierRegistry") as reg:
            reg.get.return_value = mock_mapper
            result = controller.convert(
                carrier_response={"trk_num": "123", "stat": "DELIVERED"},
                carrier="example",
            )
        assert result["tracking_number"] == "123"
        assert result["status"] == "delivered"
        mock_mapper.map_tracking_response.assert_called_once()

    def test_convert_unknown_carrier_raises_404(self):
        """convert() with unknown carrier raises HTTPException 404."""
        controller = ApiController()
        with patch("src.controller.convert.CarrierRegistry") as reg:
            reg.get.side_effect = KeyError("unknown")
            with pytest.raises(HTTPException) as exc_info:
                controller.convert(carrier_response={}, carrier="unknown")
        assert exc_info.value.status_code == 404

    def test_convert_mapper_error_raises_400(self):
        """convert() when mapper fails raises HTTPException 400."""
        controller = ApiController()
        mock_mapper = MagicMock()
        mock_mapper.map_tracking_response.side_effect = ValueError("bad payload")
        with patch("src.controller.convert.CarrierRegistry") as reg:
            reg.get.return_value = mock_mapper
            with pytest.raises(HTTPException) as exc_info:
                controller.convert(carrier_response={}, carrier="example")
        assert exc_info.value.status_code == 400


@pytest.mark.unit
class TestApiControllerExtractJobs:
    """Test ApiController get_extract_job with in-memory job store."""

    def test_get_extract_job_not_found_raises_404(self):
        """get_extract_job() with unknown job_id raises 404."""
        controller = ApiController()
        with patch.dict(_extract_jobs, {}, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                controller.get_extract_job("nonexistent")
        assert exc_info.value.status_code == 404
        assert "nonexistent" in str(exc_info.value.detail)

    def test_get_extract_job_completed_returns_result(self):
        """get_extract_job() when completed returns result dict."""
        controller = ApiController()
        job_id = "job-1"
        result_data = {"schema_version": "1.0", "schema": {}}
        with patch.dict(
            _extract_jobs,
            {job_id: {"status": "completed", "result": result_data, "error": None}},
            clear=True,
        ):
            result = controller.get_extract_job(job_id)
        assert result == result_data

    def test_get_extract_job_failed_returns_json_response(self):
        """get_extract_job() when failed returns 200 JSONResponse with error."""
        controller = ApiController()
        job_id = "job-2"
        with patch.dict(
            _extract_jobs,
            {
                job_id: {
                    "status": "failed",
                    "result": None,
                    "error": "Extraction failed",
                }
            },
            clear=True,
        ):
            result = controller.get_extract_job(job_id)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 200
        assert result.media_type == "application/json"

    def test_get_extract_job_pending_returns_202(self):
        """get_extract_job() when pending returns 202 JSONResponse."""
        controller = ApiController()
        job_id = "job-3"
        with patch.dict(
            _extract_jobs,
            {job_id: {"status": "pending", "result": None, "error": None}},
            clear=True,
        ):
            result = controller.get_extract_job(job_id)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 202


@pytest.mark.unit
class TestApiControllerCarrierOpenapi:
    """Test ApiController carrier_openapi_yaml with mocked file and generator."""

    def test_carrier_openapi_yaml_not_found_raises_404(self):
        """carrier_openapi_yaml() when schema file missing raises 404."""
        controller = ApiController()
        path_mock = MagicMock()
        path_mock.parent = path_mock
        path_mock.__truediv__ = MagicMock(return_value=path_mock)
        path_mock.exists.return_value = False
        with patch("src.controller.carriers.Path", return_value=path_mock):
            with pytest.raises(HTTPException) as exc_info:
                controller.carrier_openapi_yaml("missing")
        assert exc_info.value.status_code == 404

    def test_carrier_openapi_yaml_returns_yaml_string(self):
        """carrier_openapi_yaml() returns OpenAPI YAML string when file exists."""
        controller = ApiController()
        path_mock = MagicMock()
        path_mock.parent = path_mock
        path_mock.__truediv__ = MagicMock(return_value=path_mock)
        path_mock.exists.return_value = True
        fake_spec = {"openapi": "3.0.0", "info": {"title": "Test"}}
        file_content = '{"schema": {"name": "Test", "endpoints": []}}'
        with patch("src.controller.carriers.Path", return_value=path_mock):
            with patch("builtins.open", MagicMock()) as open_mock:
                cm = MagicMock()
                cm.read.return_value = file_content
                open_mock.return_value.__enter__.return_value = cm
                open_mock.return_value.__exit__.return_value = None
                with patch(
                    "src.controller.carriers.generate_openapi", return_value=fake_spec
                ):
                    with patch("src.controller.carriers.UniversalCarrierFormat") as ucf:
                        ucf.model_validate.return_value = MagicMock()
                        result = controller.carrier_openapi_yaml("test")
        assert "openapi" in result or "3.0" in result
