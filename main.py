"""Crypto Prime Bot v2.0 — Entry Point."""

import asyncio
import signal
from src.bootstrap.bootstrap import Bootstrap


async def main():
    bootstrap = Bootstrap()
    bootstrap.startup()

    # Start Telegram polling
    telegram_service = bootstrap.container.telegram_service
    await telegram_service.start_polling()

    # Start Scheduler
    scheduler = bootstrap.container.scheduler
    await scheduler.start()

    # Wait for shutdown signal
    stop_event = asyncio.Event()

    def signal_handler():
        stop_event.set()

    signal.signal(signal.SIGINT, lambda s, f: signal_handler())
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler())

    await stop_event.wait()

    bootstrap.shutdown()


if __name__ == "__main__":
    asyncio.run(main())