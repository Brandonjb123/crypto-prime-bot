"""Webhook Runner — placeholder untuk deployment."""

from src.infrastructure.telegram.application import TelegramApplication


class WebhookRunner:
    def __init__(self, app: TelegramApplication, url: str) -> None:
        self.app = app
        self.url = url

    async def run(self) -> None:
        # Placeholder
        pass

    async def stop(self) -> None:
        await self.app.stop()