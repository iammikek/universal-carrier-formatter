"""
LLM provider factory: build LangChain chat model from provider (openai | anthropic).

Supports env-driven provider (LLM_PROVIDER) and --provider openai|anthropic so the
brief's "LangChain or similar" is clearly multi-provider capable.
"""

import os
from typing import Any, Optional

from .config import (
    ANTHROPIC_API_KEY_ENV,
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_PROVIDER,
    OPENAI_API_KEY_ENV,
)


def get_default_model_for_provider(provider: str) -> str:
    """Return default model name for the given provider."""
    if provider == "anthropic":
        return DEFAULT_ANTHROPIC_MODEL
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
        provider: "openai" or "anthropic"
        model: Model name (default: gpt-4.1-mini for openai, claude-3-5-haiku for anthropic)
        temperature: LLM temperature
        api_key: API key (default: from OPENAI_API_KEY or ANTHROPIC_API_KEY per provider)
        **kwargs: Passed to the chat model constructor

    Returns:
        LangChain BaseChatModel (ChatOpenAI or ChatAnthropic)

    Raises:
        ValueError: If provider is unknown or API key is missing
    """
    provider = (provider or "").strip().lower() or DEFAULT_LLM_PROVIDER
    if provider not in ("openai", "anthropic"):
        raise ValueError(
            f"Unknown LLM provider: {provider!r}. Use openai or anthropic."
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        api_key = api_key or os.getenv(OPENAI_API_KEY_ENV)
        if not api_key:
            raise ValueError(
                f"{OPENAI_API_KEY_ENV} is not set. Set it in .env or pass api_key."
            )
        model = model or DEFAULT_LLM_MODEL
        model_kwargs = kwargs.pop("model_kwargs", None) or {}
        if "gpt" in model.lower() or "o1" in model.lower():
            model_kwargs["response_format"] = {"type": "json_object"}
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key,
            model_kwargs=model_kwargs if model_kwargs else None,
            **kwargs,
        )

    # anthropic
    from langchain_anthropic import ChatAnthropic

    api_key = api_key or os.getenv(ANTHROPIC_API_KEY_ENV)
    if not api_key:
        raise ValueError(
            f"{ANTHROPIC_API_KEY_ENV} is not set. Set it in .env or pass api_key."
        )
    model = model or DEFAULT_ANTHROPIC_MODEL
    return ChatAnthropic(
        model=model,
        temperature=temperature,
        api_key=api_key,
        **kwargs,
    )
