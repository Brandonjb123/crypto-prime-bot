"""Telegram Service — wrapper untuk Bot API."""

from loguru import logger
from telegram.error import BadRequest
from telegram.ext import Application


class TelegramService:
    def __init__(self, token: str) -> None:
        self.token = token
        self.app: Application | None = None

    def set_application(self, app: Application) -> None:
        """Terima Application yang sudah dibangun oleh TelegramApplication."""
        self.app = app

    async def send_message(self, chat_id: str, text: str):
        """Kirim pesan Telegram tanpa menghentikan pipeline jika chat invalid."""
        try:
            return await self.app.bot.send_message(chat_id=chat_id, text=text)
        except BadRequest as e:
            logger.warning(f"Telegram send_message gagal untuk chat_id={chat_id}: {e}")
            return None