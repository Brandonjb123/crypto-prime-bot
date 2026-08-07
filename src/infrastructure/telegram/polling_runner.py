"""Polling Runner — menjalankan Telegram Bot dalam polling mode."""

from src.infrastructure.telegram.telegram_service import TelegramService


class PollingRunner:
    def __init__(self, service: TelegramService) -> None:
        self.service = service

    async def run(self) -> None:
        await self.service.start_polling()

    async def stop(self) -> None:
        await self.service.stop()