# Security and secrets

## API keys and secrets

- **Never log or print API keys, tokens, or other secrets.** Log only whether a key is set or not (e.g. “OPENAI_API_KEY set” / “OPENAI_API_KEY not set”).
- API keys are read from environment variables (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) or from a `.env` file (not committed). Do not hardcode keys in source.
- When raising errors (e.g. “API key not set”), mention the **env var name** only, not its value.

## Logging audit

- **Codebase policy:** No `log.*`, `logger.*`, or `print` statement should output secret material. Exception messages and log messages may reference env var **names** (e.g. `OPENAI_API_KEY is not set`).
- If you add new configuration that holds secrets, read it from the environment or a secure store and do not include it in log formatters, request IDs, or error responses that might be persisted.

## Contributing

When contributing, ensure any new logging or error handling follows the above. If you find a place that might leak secrets, open an issue or fix it and note it in the PR.
