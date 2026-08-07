"""Unit tests untuk TelegramService."""

from unittest.mock import AsyncMock, MagicMock, patch

from src.infrastructure.telegram.telegram_service import TelegramService


class TestTelegramService:
    @patch("src.infrastructure.telegram.telegram_service.Application")
    async def test_start_polling(self, mock_app_class):
        # Mock the Application.builder() chain entirely
        mock_app_instance = MagicMock()
        mock_app_instance.initialize = AsyncMock()
        mock_app_instance.start = AsyncMock()
        mock_app_instance.updater = MagicMock()
        mock_app_instance.updater.start_polling = AsyncMock()

        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_app_instance
        mock_app_class.builder.return_value = mock_builder

        service = TelegramService(token="dummy")
        await service.start_polling()

        mock_app_instance.initialize.assert_awaited_once()
        mock_app_instance.start.assert_awaited_once()
        mock_app_instance.updater.start_polling.assert_awaited_once()

    async def test_stop(self):
        service = TelegramService(token="dummy")
        service.app = MagicMock()
        service.app.updater = MagicMock()
        service.app.updater.stop = AsyncMock()
        service.app.stop = AsyncMock()
        service.app.shutdown = AsyncMock()

        await service.stop()
        service.app.updater.stop.assert_awaited_once()

    async def test_send_message(self):
        service = TelegramService(token="dummy")
        service.app = MagicMock()
        service.app.bot = MagicMock()
        service.app.bot.send_message = AsyncMock()

        await service.send_message(chat_id=123, text="Hello")
        service.app.bot.send_message.assert_awaited_once_with(chat_id=123, text="Hello")

    async def test_dependency_injection(self):
        service = TelegramService(token="custom_token")
        assert service.token == "custom_token"