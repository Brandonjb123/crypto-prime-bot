"""Unit tests for Bootstrap."""

from unittest.mock import patch

import pytest

from src.bootstrap.bootstrap import Bootstrap


class TestBootstrap:
    def test_startup_success(self, monkeypatch):
        # Set required environment variables
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
        monkeypatch.setenv("TURSO_DATABASE_URL", "test_url")
        monkeypatch.setenv("TURSO_AUTH_TOKEN", "test_auth")

        bootstrap = Bootstrap()
        # Mock all steps to prevent real initialization
        with patch.object(bootstrap, "_load_config"), \
             patch.object(bootstrap, "_init_logger"), \
             patch.object(bootstrap, "_init_event_bus"), \
             patch.object(bootstrap, "_init_notification"), \
             patch.object(bootstrap, "_init_telegram"), \
             patch.object(bootstrap, "_init_exchange"), \
             patch.object(bootstrap, "_init_pipeline"), \
             patch.object(bootstrap, "_init_scheduler"):
            bootstrap.startup()  # Should complete without error
            assert True

    def test_startup_config_failure(self):
        bootstrap = Bootstrap()
        with patch.object(bootstrap, "_load_config", side_effect=Exception("Config error")):
            with pytest.raises(SystemExit):
                bootstrap.startup()

    def test_container_created(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
        monkeypatch.setenv("TURSO_DATABASE_URL", "test_url")
        monkeypatch.setenv("TURSO_AUTH_TOKEN", "test_auth")

        bootstrap = Bootstrap()
        assert bootstrap.container is not None
        assert bootstrap.container.event_bus is not None
        assert bootstrap.container.position_repo is not None