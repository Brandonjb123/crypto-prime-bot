import pytest

from src.config.validator import ConfigurationError, validate_config


class TestConfigValidator:
    def test_missing_config_raises_error(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
        monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
        with pytest.raises(ConfigurationError):
            validate_config()

    def test_valid_config_passes(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
        monkeypatch.setenv("TURSO_DATABASE_URL", "test_url")
        monkeypatch.setenv("TURSO_AUTH_TOKEN", "test_auth")
        validate_config()  # no error = pass

    def test_partial_missing(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
        monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
        with pytest.raises(ConfigurationError):
            validate_config()

    def test_unknown_config_ignored(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test")
        monkeypatch.setenv("TURSO_DATABASE_URL", "test")
        monkeypatch.setenv("TURSO_AUTH_TOKEN", "test")
        monkeypatch.setenv("UNKNOWN_VAR", "value")
        validate_config()  # should not raise