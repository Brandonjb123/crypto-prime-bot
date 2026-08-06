from src.core.types.enums import TelegramResponseType
from src.telegram.bot import TelegramBot


class TestTelegramBot:
    def test_allowed_user(self, monkeypatch):
        monkeypatch.setattr("src.telegram.bot.TELEGRAM_ALLOWED_USERS", ["123"])
        bot = TelegramBot()
        resp = bot.handle_message("/status", "123")
        assert resp.response_type == TelegramResponseType.TEXT

    def test_blocked_user(self, monkeypatch):
        monkeypatch.setattr("src.telegram.bot.TELEGRAM_ALLOWED_USERS", ["123"])
        bot = TelegramBot()
        resp = bot.handle_message("/status", "999")
        assert resp.response_type == TelegramResponseType.ERROR
        assert "Unauthorized" in resp.text