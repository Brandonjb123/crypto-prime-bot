"""Polling Runner — menjalankan Telegram Bot dalam polling mode."""

from src.infrastructure.telegram.application import TelegramApplication
from src.logging.logger import get_logger

logger = get_logger("telegram.polling")

class PollingRunner:
    def __init__(self, app: TelegramApplication) -> None:
        self.app = app

    async def run(self) -> None:
        logger.info("Starting Telegram polling...")
        await self.app.start_polling()

    async def stop(self) -> None:
        await self.app.stop()