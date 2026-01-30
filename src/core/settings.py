"""
Structured settings: single place for env-based configuration (imp-7).

Reads and validates API keys, provider, timeouts, and limits from environment.
Use get_settings() for a cached instance. Never log secret values; log only
"key set" / "key not set" (see docs/SECURITY.md).
"""

import os
from typing import Optional

from .config import (
    ANTHROPIC_API_KEY_ENV,
    DEFAULT_LLM_PROVIDER,
    LLM_PROVIDER_ENV,
    OPENAI_API_KEY_ENV,
)


def _int_env(name: str, default: int) -> int:
    """Read integer from env; on invalid value return default."""
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


class Settings:
    """
    Environment-driven settings for the formatter (API keys, provider, timeouts).

    All secret values are read from env; never log or expose raw keys.
    """

    def __init__(self) -> None:
        self._openai_api_key: Optional[str] = None
        self._anthropic_api_key: Optional[str] = None
        self._llm_provider: Optional[str] = None
        self._extract_timeout_seconds: Optional[int] = None

    @property
    def openai_api_key(self) -> Optional[str]:
        """OPENAI_API_KEY from env (never log the value)."""
        if self._openai_api_key is None:
            self._openai_api_key = os.environ.get(OPENAI_API_KEY_ENV) or None
        return self._openai_api_key if self._openai_api_key else None

    @property
    def anthropic_api_key(self) -> Optional[str]:
        """ANTHROPIC_API_KEY from env (never log the value)."""
        if self._anthropic_api_key is None:
            self._anthropic_api_key = os.environ.get(ANTHROPIC_API_KEY_ENV) or None
        return self._anthropic_api_key if self._anthropic_api_key else None

    @property
    def llm_provider(self) -> str:
        """LLM_PROVIDER from env (openai | anthropic | azure), default openai."""
        if self._llm_provider is None:
            raw = (
                (os.environ.get(LLM_PROVIDER_ENV) or DEFAULT_LLM_PROVIDER)
                .strip()
                .lower()
            )
            self._llm_provider = (
                raw if raw in ("openai", "anthropic", "azure") else DEFAULT_LLM_PROVIDER
            )
        return self._llm_provider

    @property
    def extract_timeout_seconds(self) -> int:
        """EXTRACT_TIMEOUT_SECONDS from env (default 300), must be positive."""
        if self._extract_timeout_seconds is None:
            val = _int_env("EXTRACT_TIMEOUT_SECONDS", 300)
            self._extract_timeout_seconds = max(1, val)
        return self._extract_timeout_seconds

    def openai_api_key_set(self) -> bool:
        """True if OPENAI_API_KEY is set (safe to log)."""
        return bool(self.openai_api_key)

    def anthropic_api_key_set(self) -> bool:
        """True if ANTHROPIC_API_KEY is set (safe to log)."""
        return bool(self.anthropic_api_key)


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Return cached Settings instance (reads env on first access)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
