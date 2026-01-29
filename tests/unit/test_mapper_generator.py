"""
Tests for Mapper Generator Service.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.schema import (
    AuthenticationMethod,
    Endpoint,
    HttpMethod,
    RateLimit,
    RequestSchema,
    ResponseSchema,
    UniversalCarrierFormat,
)
from src.mapper_generator import MapperGeneratorService


@pytest.mark.unit
class TestMapperGeneratorService:
    """Test MapperGeneratorService."""

    @pytest.fixture
    def generator(self):
        """Create generator instance with mocked LLM."""
        with patch("src.mapper_generator.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm_class.return_value = mock_llm
            gen = MapperGeneratorService(api_key="test-key")
            gen.llm = mock_llm
            return gen

    @pytest.fixture
    def sample_schema(self):
        """Create a sample UniversalCarrierFormat schema."""
        return UniversalCarrierFormat(
            name="Test Carrier",
            base_url="https://api.test.com",
            version="v1",
            description="Test carrier API",
            endpoints=[
                Endpoint(
                    path="/track",
                    method=HttpMethod.GET,
                    summary="Track shipment",
                    request=RequestSchema(
                        parameters=[],
                    ),
                    responses=[
                        ResponseSchema(
                            status_code=200,
                            description="Success",
                        )
                    ],
                )
            ],
            authentication=[
                AuthenticationMethod(
                    type="api_key",
                    name="API Key",
                    location="header",
                    parameter_name="X-API-Key",
                )
            ],
            rate_limits=[RateLimit(requests=100, period="1 minute")],
        )

    def test_carrier_name_to_class_name(self, generator):
        """Test carrier name to class name conversion."""
        assert generator._carrier_name_to_class_name("DHL Express") == "DhlExpress"
        assert generator._carrier_name_to_class_name("FedEx") == "Fedex"
        assert generator._carrier_name_to_class_name("fedex") == "Fedex"
        assert generator._carrier_name_to_class_name("ups-express") == "UpsExpress"

    def test_carrier_name_to_slug(self, generator):
        """Test carrier name to registry slug conversion."""
        assert generator._carrier_name_to_slug("DHL Express") == "dhl_express"
        assert generator._carrier_name_to_slug("MYDHL API") == "mydhl_api"
        assert generator._carrier_name_to_slug("Royal Mail") == "royal_mail"

    def test_extract_code_from_response_plain(self, generator):
        """Test extracting code from plain response."""
        response = "class TestMapper:\n    pass"
        result = generator._extract_code_from_response(response)
        assert result == response

    def test_extract_code_from_response_markdown(self, generator):
        """Test extracting code from markdown code block."""
        response = "```python\nclass TestMapper:\n    pass\n```"
        result = generator._extract_code_from_response(response)
        assert "class TestMapper" in result
        assert "```" not in result

    def test_extract_code_from_response_no_lang(self, generator):
        """Test extracting code from code block without language."""
        response = "```\nclass TestMapper:\n    pass\n```"
        result = generator._extract_code_from_response(response)
        assert "class TestMapper" in result
        assert "```" not in result

    def test_clean_generated_code_adds_imports(self, generator):
        """Test cleaning code adds missing imports."""
        code = "class TestMapper:\n    pass"
        result = generator._clean_generated_code(code, "Test Carrier")
        assert "from ..core.schema import" in result

    def test_clean_generated_code_preserves_existing_imports(self, generator):
        """Test cleaning code preserves existing imports."""
        code = "from ..core.schema import UniversalCarrierFormat\n\nclass TestMapper:\n    pass"
        result = generator._clean_generated_code(code, "Test Carrier")
        assert "from ..core.schema import UniversalCarrierFormat" in result

    def test_generate_mapper_success(self, generator, sample_schema, tmp_path):
        """Test successful mapper generation."""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = """
from typing import Any, Dict
from ..core.schema import UniversalCarrierFormat

class TestCarrierMapper:
    FIELD_MAPPING = {}

    def map_tracking_response(self, carrier_response: Dict[str, Any]) -> Dict[str, Any]:
        return {}
"""
        generator.llm.invoke.return_value = mock_response

        output_path = tmp_path / "test_mapper.py"
        result = generator.generate_mapper(sample_schema, output_path=output_path)

        assert "class TestCarrierMapper" in result
        assert output_path.exists()
        assert "TestCarrierMapper" in output_path.read_text()

    def test_generate_mapper_without_output_path(self, generator, sample_schema):
        """Test mapper generation without saving to file."""
        mock_response = MagicMock()
        mock_response.content = "class TestCarrierMapper:\n    pass"
        generator.llm.invoke.return_value = mock_response

        result = generator.generate_mapper(sample_schema)

        assert "TestCarrierMapper" in result

    def test_generate_mapper_llm_error(self, generator, sample_schema):
        """Test mapper generation handles LLM errors."""
        generator.llm.invoke.side_effect = Exception("LLM API error")

        with pytest.raises(ValueError, match="Failed to generate mapper"):
            generator.generate_mapper(sample_schema)

    def test_generate_mapper_creates_output_directory(
        self, generator, sample_schema, tmp_path
    ):
        """Test mapper generation creates output directory if needed."""
        mock_response = MagicMock()
        mock_response.content = "class TestCarrierMapper:\n    pass"
        generator.llm.invoke.return_value = mock_response

        output_path = tmp_path / "nested" / "dir" / "mapper.py"
        generator.generate_mapper(sample_schema, output_path=output_path)

        assert output_path.exists()

    def test_clean_generated_code_detects_duplicate_keys(self, generator):
        """Test cleaning code detects duplicate keys in FIELD_MAPPING."""
        code = """
class TestMapper:
    FIELD_MAPPING = {
        "field1": UniversalFieldNames.TRACKING_NUMBER,
        "field2": UniversalFieldNames.STATUS,
        "field1": UniversalFieldNames.STATUS,  # Duplicate key
    }
"""
        with patch("src.mapper_generator.logger") as mock_logger:
            generator._clean_generated_code(code, "Test Carrier")
            # Should warn about duplicate keys
            mock_logger.warning.assert_called()
            warning_call = str(mock_logger.warning.call_args)
            assert "duplicate" in warning_call.lower() or "Duplicate" in warning_call

    def test_clean_generated_code_no_duplicates(self, generator):
        """Test cleaning code with no duplicate keys."""
        code = """
class TestMapper:
    FIELD_MAPPING = {
        "field1": UniversalFieldNames.TRACKING_NUMBER,
        "field2": UniversalFieldNames.STATUS,
    }
"""
        with patch("src.mapper_generator.logger") as mock_logger:
            generator._clean_generated_code(code, "Test Carrier")
            # Should not warn about duplicates
            warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
            duplicate_warnings = [w for w in warning_calls if "duplicate" in w.lower()]
            assert len(duplicate_warnings) == 0

    def test_clean_generated_code_removes_duplicate_field_mapping_keys(self, generator):
        """Test that duplicate keys in FIELD_MAPPING are removed (first occurrence kept)."""
        code = """
class TestCarrierMapper:
    FIELD_MAPPING = {
        "AWBNumber": UniversalFieldNames.TRACKING_NUMBER,
        "CountryCode": UniversalFieldNames.COUNTRY,
        "PostalCode": UniversalFieldNames.POSTAL_CODE,
        "VolumetricWeight": UniversalFieldNames.WEIGHT,
        "WeightUnit": "weight_unit",
        "ShipmentIdentificationNumber": UniversalFieldNames.SHIPMENT_NUMBER,
        "CountryCode": UniversalFieldNames.DESTINATION_COUNTRY,
        "VolumetricWeight": UniversalFieldNames.WEIGHT,
        "ShipmentIdentificationNumber": UniversalFieldNames.SHIPMENT_NUMBER,
    }
"""
        result = generator._clean_generated_code(code, "Test Carrier")
        # Count occurrences of each key in FIELD_MAPPING
        import re

        content = re.search(r"FIELD_MAPPING\s*=\s*\{([^}]+)\}", result, re.DOTALL)
        assert content is not None
        keys = re.findall(r'"([^"]+)"\s*:', content.group(1))
        assert keys.count("AWBNumber") == 1
        assert keys.count("CountryCode") == 1
        assert keys.count("PostalCode") == 1
        assert keys.count("VolumetricWeight") == 1
        assert keys.count("WeightUnit") == 1
        assert keys.count("ShipmentIdentificationNumber") == 1
        assert len(keys) == 6

    def test_clean_generated_code_handles_missing_field_mapping(self, generator):
        """Test cleaning code handles missing FIELD_MAPPING."""
        code = "class TestMapper:\n    pass"
        result = generator._clean_generated_code(code, "Test Carrier")
        # Should not crash
        assert "class TestMapper" in result

    def test_clean_generated_code_injects_registry_pattern(self, generator):
        """Test cleaning code injects CarrierMapperBase and @register_carrier when class name matches."""
        code = """from ..core.schema import UniversalCarrierFormat
from ..core import UniversalFieldNames

class TestCarrierMapper:
    FIELD_MAPPING = {}
    def map_tracking_response(self, carrier_response):
        return {}
"""
        result = generator._clean_generated_code(code, "Test Carrier")
        assert "from .base import CarrierMapperBase" in result
        assert "from .registry import register_carrier" in result
        assert '@register_carrier("test_carrier")' in result
        assert "class TestCarrierMapper(CarrierMapperBase):" in result

    def test_clean_generated_code_imports_ordered_and_stable(self, generator):
        """Generated mapper imports are ordered and stable: core before base before registry."""
        code = """
class TestCarrierMapper:
    FIELD_MAPPING = {}
    def map_tracking_response(self, carrier_response):
        return {}
"""
        result = generator._clean_generated_code(code, "Test Carrier")
        lines = result.split("\n")
        # All imports should appear before the first class/def
        first_non_import = next(
            (
                i
                for i, line in enumerate(lines)
                if line.strip()
                and not line.strip().startswith("from ")
                and not line.strip().startswith("import ")
                and not line.strip().startswith("#")
            ),
            len(lines),
        )
        for i, line in enumerate(lines):
            if (
                line.strip().startswith("from ") or line.strip().startswith("import ")
            ) and i > first_non_import:
                pytest.fail(f"Import line after non-import content: {line!r}")
        # Order: core.schema, then core UniversalFieldNames, then base, then registry
        text = result
        idx_core_schema = text.find("from ..core.schema import")
        idx_universal = text.find("from ..core import UniversalFieldNames")
        idx_base = text.find("from .base import CarrierMapperBase")
        idx_registry = text.find("from .registry import register_carrier")
        assert idx_core_schema >= 0
        assert idx_universal >= 0
        assert idx_base >= 0
        assert idx_registry >= 0
        assert idx_core_schema < idx_base
        assert idx_universal < idx_base
        assert idx_base < idx_registry

    def test_clean_generated_code_dedupe_keeps_first_value_regression(self, generator):
        """Regression: duplicate FIELD_MAPPING key keeps first occurrence value (not second)."""
        code = """
class TestCarrierMapper:
    FIELD_MAPPING = {
        "CountryCode": UniversalFieldNames.COUNTRY,
        "PostalCode": UniversalFieldNames.POSTAL_CODE,
        "CountryCode": UniversalFieldNames.DESTINATION_COUNTRY,
    }
"""
        result = generator._clean_generated_code(code, "Test Carrier")
        # CountryCode should appear once and map to COUNTRY (first), not DESTINATION_COUNTRY
        assert "CountryCode" in result
        assert "UniversalFieldNames.COUNTRY" in result
        # The line for CountryCode should be the first mapping (COUNTRY)
        import re

        content = re.search(r"FIELD_MAPPING\s*=\s*\{([^}]+)\}", result, re.DOTALL)
        assert content is not None
        mapping_block = content.group(1)
        assert "CountryCode" in mapping_block
        # First occurrence is COUNTRY; duplicate DESTINATION_COUNTRY should be removed
        assert mapping_block.count("CountryCode") == 1
        # The kept value for CountryCode must be COUNTRY (first), not DESTINATION_COUNTRY
        lines_in_block = [ln for ln in mapping_block.split("\n") if "CountryCode" in ln]
        assert len(lines_in_block) == 1
        assert "COUNTRY" in lines_in_block[0]
        assert "DESTINATION_COUNTRY" not in lines_in_block[0]
