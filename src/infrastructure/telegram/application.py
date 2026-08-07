"""Telegram Application — entry point untuk Bot."""

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config.constants import TELEGRAM_BOT_TOKEN
from src.telegram.bot import TelegramBot


class TelegramApplication:
    def __init__(self, bot: TelegramBot, token: str | None = None) -> None:
        self.bot = bot
        self.token = token or TELEGRAM_BOT_TOKEN
        self.app = None

    def build(self) -> None:
        if not self.token:
            return
        self.app = ApplicationBuilder().token(self.token).build()
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.bot.handle_update))
        self.app.add_handler(CommandHandler("status", self.bot.handle_update))
        self.app.add_handler(CommandHandler("positions", self.bot.handle_update))
        self.app.add_handler(CommandHandler("portfolio", self.bot.handle_update))
        self.app.add_handler(CommandHandler("help", self.bot.handle_update))
        self.app.add_handler(CommandHandler("lastsignal", self.bot.handle_update))

    async def start_polling(self) -> None:
        if not self.app:
            self.build()
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

    async def stop(self) -> None:
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()