"""Crypto Prime Bot v2.0 — Entry Point."""

import asyncio
import signal

from src.bootstrap.bootstrap import Bootstrap
from src.infrastructure.telegram.application import TelegramApplication
from src.infrastructure.telegram.polling_runner import PollingRunner


async def main():
    bootstrap = Bootstrap()
    bootstrap.startup()

    container = bootstrap.container

    # Start scheduler dulu (jangan block)
    scheduler = container.scheduler
    await scheduler.start()

    # Telegram polling sebagai task terpisah
    telegram_app = TelegramApplication(
        bot=container.telegram_bot,
        service=container.telegram_service,
    )
    telegram_app.build()
    runner = PollingRunner(telegram_app)
    telegram_task = asyncio.create_task(runner.run())

    # Graceful shutdown
    stop_event = asyncio.Event()

    def signal_handler():
        stop_event.set()

    signal.signal(signal.SIGINT, lambda s, f: signal_handler())
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler())

    await stop_event.wait()

    telegram_task.cancel()
    await scheduler.stop()
    await bootstrap.shutdown()


if __name__ == "__main__":
    asyncio.run(main())