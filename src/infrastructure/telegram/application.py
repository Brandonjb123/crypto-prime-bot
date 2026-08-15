"""Telegram Application — entry point untuk Bot."""

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config.settings import settings
from src.infrastructure.telegram.telegram_service import TelegramService
from src.telegram.bot import TelegramBot


class TelegramApplication:
    def __init__(self, bot: TelegramBot, service: TelegramService) -> None:
        self.bot = bot
        self.service = service
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.app = None

    def build(self) -> None:
        if not self.token:
            return
        self.app = ApplicationBuilder().token(self.token).build()
        self.app.add_handler(CommandHandler("start", self.bot.handle_update))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.bot.handle_update))
        self.app.add_handler(CommandHandler("status", self.bot.handle_update))
        self.app.add_handler(CommandHandler("positions", self.bot.handle_update))
        self.app.add_handler(CommandHandler("portfolio", self.bot.handle_update))
        self.app.add_handler(CommandHandler("help", self.bot.handle_update))
        self.app.add_handler(CommandHandler("lastsignal", self.bot.handle_update))
        self.app.add_handler(CallbackQueryHandler(self.bot.handle_callback))

        self.service.set_application(self.app)

    async def start_polling(self) -> None:
        if not self.app:
            self.build()
        if self.app:
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()

    async def stop(self) -> None:
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()