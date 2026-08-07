"""Telegram Service — wrapper untuk Bot API."""

from telegram.ext import Application
from config.constants import TELEGRAM_BOT_TOKEN


class TelegramService:
    def __init__(self, token: str | None = None) -> None:
        self.token = token or TELEGRAM_BOT_TOKEN
        self.app: Application | None = None

    async def start_polling(self) -> None:
        if not self.token:
            return
        self.app = Application.builder().token(self.token).build()
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

    async def start_webhook(self, url: str) -> None:
        # Placeholder untuk deployment
        pass

    async def stop(self) -> None:
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()

    async def send_message(self, chat_id: int, text: str) -> None:
        if self.app and self.app.bot:
            await self.app.bot.send_message(chat_id=chat_id, text=text)