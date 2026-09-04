"""Unit tests untuk PollingRunner."""

from unittest.mock import AsyncMock, MagicMock

from src.infrastructure.telegram.polling_runner import PollingRunner


class TestPollingRunner:
    async def test_run_starts_polling(self):
        app = MagicMock()
        app.start_polling = AsyncMock()
        runner = PollingRunner(app)
        await runner.run()
        app.start_polling.assert_awaited_once()

    async def test_stop_stops_service(self):
        app = MagicMock()
        app.stop = AsyncMock()
        runner = PollingRunner(app)
        await runner.stop()
        app.stop.assert_awaited_once()