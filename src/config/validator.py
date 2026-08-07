"""Configuration validator."""

import os


class ConfigurationError(Exception):
    pass


def validate_config() -> None:
    required = [
        "TELEGRAM_BOT_TOKEN",
        "ANTHROPIC_API_KEY",
        "TURSO_DATABASE_URL",
        "TURSO_AUTH_TOKEN",
    ]

    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ConfigurationError(f"Missing required environment variables: {', '.join(missing)}")