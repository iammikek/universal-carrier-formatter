"""
Unit tests for LLM provider factory.

Tests get_chat_model(provider=openai|anthropic), get_default_model_for_provider,
and ValueError for unknown provider. Mocks external packages to avoid real API calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.config import (
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_LLM_MODEL,
)
from src.core.llm_factory import get_chat_model, get_default_model_for_provider


@pytest.mark.unit
class TestGetDefaultModelForProvider:
    """Test get_default_model_for_provider."""

    def test_openai_returns_default_openai_model(self):
        assert get_default_model_for_provider("openai") == DEFAULT_LLM_MODEL

    def test_anthropic_returns_default_anthropic_model(self):
        assert get_default_model_for_provider("anthropic") == DEFAULT_ANTHROPIC_MODEL

    def test_unknown_provider_returns_openai_default(self):
        # Implementation returns DEFAULT_LLM_MODEL for any non-anthropic
        assert get_default_model_for_provider("unknown") == DEFAULT_LLM_MODEL


@pytest.mark.unit
class TestGetChatModel:
    """Test get_chat_model with mocked LangChain imports."""

    @patch("langchain_openai.ChatOpenAI")
    def test_openai_returns_chat_openai(self, mock_chat_openai_class):
        mock_instance = MagicMock()
        mock_chat_openai_class.return_value = mock_instance

        result = get_chat_model(provider="openai", api_key="sk-test")

        mock_chat_openai_class.assert_called_once()
        assert result is mock_instance
        call_kwargs = mock_chat_openai_class.call_args[1]
        assert call_kwargs["model"] == DEFAULT_LLM_MODEL
        assert call_kwargs["api_key"] == "sk-test"
        assert call_kwargs["temperature"] == 0.0

    @patch("langchain_anthropic.ChatAnthropic")
    def test_anthropic_returns_chat_anthropic(self, mock_chat_anthropic_class):
        mock_instance = MagicMock()
        mock_chat_anthropic_class.return_value = mock_instance

        result = get_chat_model(provider="anthropic", api_key="sk-ant-test")

        mock_chat_anthropic_class.assert_called_once()
        assert result is mock_instance
        call_kwargs = mock_chat_anthropic_class.call_args[1]
        assert call_kwargs["model"] == DEFAULT_ANTHROPIC_MODEL
        assert call_kwargs["api_key"] == "sk-ant-test"
        assert call_kwargs["temperature"] == 0.0

    def test_unknown_provider_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_chat_model(provider="unknown", api_key="sk-test")

    def test_empty_provider_defaults_to_openai(self):
        with patch("langchain_openai.ChatOpenAI") as mock_openai:
            mock_openai.return_value = MagicMock()
            with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-env"}):
                get_chat_model(provider="", api_key=None)
            mock_openai.assert_called_once()

    @patch("langchain_openai.ChatOpenAI")
    def test_openai_without_api_key_raises_when_env_unset(self, mock_chat_openai_class):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
                get_chat_model(provider="openai", api_key=None)

    @patch("langchain_anthropic.ChatAnthropic")
    def test_anthropic_without_api_key_raises_when_env_unset(
        self, mock_chat_anthropic_class
    ):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is not set"):
                get_chat_model(provider="anthropic", api_key=None)

    @patch("langchain_openai.ChatOpenAI")
    def test_openai_uses_env_api_key_when_not_passed(self, mock_chat_openai_class):
        mock_chat_openai_class.return_value = MagicMock()
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-from-env"}):
            get_chat_model(provider="openai")
        call_kwargs = mock_chat_openai_class.call_args[1]
        assert call_kwargs["api_key"] == "sk-from-env"
