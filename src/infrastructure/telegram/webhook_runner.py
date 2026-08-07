"""Webhook Runner — placeholder untuk deployment."""

from src.infrastructure.telegram.telegram_service import TelegramService


class WebhookRunner:
    def __init__(self, service: TelegramService, url: str) -> None:
        self.service = service
        self.url = url

    async def run(self) -> None:
        await self.service.start_webhook(self.url)

    async def stop(self) -> None:
        await self.service.stop()