"""Unit tests untuk validasi konfigurasi LIVE."""

import pytest

from config.settings import Settings


class TestLiveConfigValidation:
    def _make_settings(self, **overrides):
        base = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "ADMIN_CHAT_ID": 123456789,
            "OPENROUTER_API_KEY": "test-llm",
            "TURSO_DATABASE_URL": "libsql://test",
            "TURSO_AUTH_TOKEN": "test-token",
            "TRADING_MODE": "PAPER",
            "LIVE_TRADING_ENABLED": False,
            "EXCHANGE_ENV": "TESTNET",
            "EXCHANGE_API_KEY": "",
            "EXCHANGE_API_SECRET": "",
        }
        base.update(overrides)
        return base

    def test_paper_without_credentials_passes(self):
        s = Settings(**self._make_settings())
        assert s.TRADING_MODE.upper() == "PAPER"

    def test_live_with_valid_testnet_passes(self):
        s = Settings(**self._make_settings(
            TRADING_MODE="LIVE",
            LIVE_TRADING_ENABLED=True,
            EXCHANGE_API_KEY="key",
            EXCHANGE_API_SECRET="secret",
        ))
        assert s.TRADING_MODE.upper() == "LIVE"

    def test_live_without_api_key_fails(self):
        with pytest.raises(ValueError):
            Settings(**self._make_settings(
                TRADING_MODE="LIVE",
                LIVE_TRADING_ENABLED=True,
                EXCHANGE_API_KEY="",
                EXCHANGE_API_SECRET="secret",
            ))

    def test_live_without_api_secret_fails(self):
        with pytest.raises(ValueError):
            Settings(**self._make_settings(
                TRADING_MODE="LIVE",
                LIVE_TRADING_ENABLED=True,
                EXCHANGE_API_KEY="key",
                EXCHANGE_API_SECRET="",
            ))

    def test_live_disabled_fails(self):
        with pytest.raises(ValueError):
            Settings(**self._make_settings(
                TRADING_MODE="LIVE",
                LIVE_TRADING_ENABLED=False,
                EXCHANGE_API_KEY="key",
                EXCHANGE_API_SECRET="secret",
            ))

    def test_live_production_fails(self):
        with pytest.raises(ValueError):
            Settings(**self._make_settings(
                TRADING_MODE="LIVE",
                LIVE_TRADING_ENABLED=True,
                EXCHANGE_ENV="PRODUCTION",
                EXCHANGE_API_KEY="key",
                EXCHANGE_API_SECRET="secret",
            ))