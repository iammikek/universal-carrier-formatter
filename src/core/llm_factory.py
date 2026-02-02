"""
LLM provider factory: build LangChain chat model from provider (openai | anthropic | azure).

Supports env-driven provider (LLM_PROVIDER) and --provider openai|anthropic|azure so the
brief's "LangChain or similar" is clearly multi-provider capable.
"""

import os
from typing import Any, Dict, Optional

from .config import (
    ANTHROPIC_API_KEY_ENV,
    AZURE_OPENAI_API_KEY_ENV,
    AZURE_OPENAI_API_VERSION_ENV,
    AZURE_OPENAI_DEPLOYMENT_ENV,
    AZURE_OPENAI_ENDPOINT_ENV,
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_AZURE_OPENAI_API_VERSION,
    DEFAULT_AZURE_OPENAI_DEPLOYMENT,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_PROVIDER,
    OPENAI_API_KEY_ENV,
)


def get_default_model_for_provider(provider: str) -> str:
    """Return default model/deployment name for the given provider."""
    if provider == "anthropic":
        return DEFAULT_ANTHROPIC_MODEL
    if provider == "azure":
        return os.environ.get(
            AZURE_OPENAI_DEPLOYMENT_ENV, DEFAULT_AZURE_OPENAI_DEPLOYMENT
        )
    return DEFAULT_LLM_MODEL


def get_chat_model(
    provider: str,
    model: Optional[str] = None,
    temperature: float = 0.0,
    api_key: Optional[str] = None,
    **kwargs: Any,
):
    """
    Return a LangChain chat model for the given provider.

    Args:
        provider: "openai", "anthropic", or "azure"
        model: Model/deployment name (default: provider-specific)
        temperature: LLM temperature
        api_key: API key (default: from env per provider)
        **kwargs: Passed to the chat model constructor

    Returns:
        LangChain BaseChatModel (ChatOpenAI, ChatAnthropic, or AzureChatOpenAI)

    Raises:
        ValueError: If provider is unknown or required credentials are missing
    """
    provider = (provider or "").strip().lower() or DEFAULT_LLM_PROVIDER
    if provider not in ("openai", "anthropic", "azure"):
        raise ValueError(
            f"Unknown LLM provider: {provider!r}. Use openai, anthropic, or azure."
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        api_key = api_key or os.getenv(OPENAI_API_KEY_ENV)
        if not api_key:
            raise ValueError(
                f"{OPENAI_API_KEY_ENV} is not set. Set it in .env or pass api_key."
            )
        model = model or DEFAULT_LLM_MODEL
        model_kwargs: Dict[str, Any] = kwargs.pop("model_kwargs", None) or {}
        if "gpt" in model.lower() or "o1" in model.lower():
            model_kwargs["response_format"] = {"type": "json_object"}
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key,  # type: ignore[arg-type]
            model_kwargs=model_kwargs if model_kwargs else None,  # type: ignore[arg-type]
            **kwargs,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        api_key = api_key or os.getenv(ANTHROPIC_API_KEY_ENV)
        if not api_key:
            raise ValueError(
                f"{ANTHROPIC_API_KEY_ENV} is not set. Set it in .env or pass api_key."
            )
        model = model or DEFAULT_ANTHROPIC_MODEL
        return ChatAnthropic(
            model=model,  # type: ignore[call-arg]
            temperature=temperature,
            api_key=api_key,  # type: ignore[arg-type]
            **kwargs,
        )

    # azure (imp-21): Azure OpenAI via langchain-openai
    from langchain_openai import AzureChatOpenAI

    api_key = api_key or os.getenv(AZURE_OPENAI_API_KEY_ENV)
    endpoint = os.getenv(AZURE_OPENAI_ENDPOINT_ENV)
    if not api_key:
        raise ValueError(
            f"{AZURE_OPENAI_API_KEY_ENV} is not set. Set it in .env or pass api_key."
        )
    if not endpoint:
        raise ValueError(
            f"{AZURE_OPENAI_ENDPOINT_ENV} is not set. Set your Azure OpenAI endpoint in .env."
        )
    deployment = model or os.getenv(
        AZURE_OPENAI_DEPLOYMENT_ENV, DEFAULT_AZURE_OPENAI_DEPLOYMENT
    )
    api_version = os.getenv(
        AZURE_OPENAI_API_VERSION_ENV, DEFAULT_AZURE_OPENAI_API_VERSION
    )
    return AzureChatOpenAI(
        azure_deployment=deployment,
        azure_endpoint=endpoint.rstrip("/"),
        api_key=api_key,  # type: ignore[arg-type]
        api_version=api_version,
        temperature=temperature,
        **kwargs,
    )
