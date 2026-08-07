from unittest.mock import AsyncMock, MagicMock
from src.telegram.bot import TelegramBot


class TestTelegramBot:
    async def test_allowed_user(self, monkeypatch):
        monkeypatch.setattr("src.telegram.bot.TELEGRAM_ALLOWED_USERS", ["123"])
        bot = TelegramBot()

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "/status"
        update.effective_chat.id = 123
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        await bot.handle_update(update, context)
        # Should not have replied with "Unauthorized"
        if update.message.reply_text.called:
            args, kwargs = update.message.reply_text.call_args
            assert args[0] != "⛔ Unauthorized"

    async def test_blocked_user(self, monkeypatch):
        monkeypatch.setattr("src.telegram.bot.TELEGRAM_ALLOWED_USERS", ["123"])
        bot = TelegramBot()

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "/status"
        update.effective_chat.id = 999
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        await bot.handle_update(update, context)
        update.message.reply_text.assert_awaited_once_with("⛔ Unauthorized")