"""Unit tests untuk PollingRunner."""

from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.telegram.polling_runner import PollingRunner


class TestPollingRunner:
    async def test_run_starts_polling(self):
        service = MagicMock()
        service.start_polling = AsyncMock()
        runner = PollingRunner(service)
        await runner.run()
        service.start_polling.assert_awaited_once()

    async def test_stop_stops_service(self):
        service = MagicMock()
        service.stop = AsyncMock()
        runner = PollingRunner(service)
        await runner.stop()
        service.stop.assert_awaited_once()