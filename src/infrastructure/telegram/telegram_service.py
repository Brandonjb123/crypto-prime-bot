"""Telegram Service — wrapper untuk Bot API."""

from telegram.ext import Application


class TelegramService:
    def __init__(self, token: str) -> None:
        self.token = token
        self.app: Application | None = None

    def set_application(self, app: Application) -> None:
        """Terima Application yang sudah dibangun oleh TelegramApplication."""
        self.app = app

    async def send_message(self, chat_id: int, text: str) -> None:
        if self.app and self.app.bot:
            await self.app.bot.send_message(chat_id=chat_id, text=text)