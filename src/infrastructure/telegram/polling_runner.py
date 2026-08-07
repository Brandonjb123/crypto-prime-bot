"""Polling Runner — menjalankan Telegram Bot dalam polling mode."""

from src.infrastructure.telegram.application import TelegramApplication


class PollingRunner:
    def __init__(self, app: TelegramApplication) -> None:
        self.app = app

    async def run(self) -> None:
        await self.app.start_polling()

    async def stop(self) -> None:
        await self.app.stop()