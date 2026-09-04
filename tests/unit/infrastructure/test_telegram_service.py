"""Unit tests untuk TelegramService."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram.error import BadRequest

from src.infrastructure.telegram.telegram_service import TelegramService


@pytest.mark.asyncio
async def test_send_message_bad_request_chat_not_found_is_graceful():
    service = TelegramService(token="test_token")

    bot = MagicMock()
    bot.send_message = AsyncMock(side_effect=BadRequest("Chat not found"))

    app = MagicMock()
    app.bot = bot
    service.set_application(app)

    result = await service.send_message("999999", "test")

    assert result is None
    bot.send_message.assert_awaited_once()

class TestTelegramService:
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

    async def test_set_application(self):
        service = TelegramService(token="dummy")
        mock_app = MagicMock()
        service.set_application(mock_app)
        assert service.app == mock_app