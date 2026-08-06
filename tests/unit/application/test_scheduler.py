"""Unit tests untuk SimpleScheduler."""

import asyncio
from unittest.mock import AsyncMock
from src.application.scheduler import SimpleScheduler


class TestSimpleScheduler:
    async def test_run_once(self):
        orch = AsyncMock()
        orch.run = AsyncMock()
        sched = SimpleScheduler(orch, interval_seconds=1)
        ctx = await sched.run_once("BTC")
        orch.run.assert_called_once_with("BTC", "4h")

    async def test_start_stop(self):
        orch = AsyncMock()
        orch.run = AsyncMock()
        sched = SimpleScheduler(orch, interval_seconds=60)
        await sched.start()
        await asyncio.sleep(0.1)
        await sched.stop()
        # Tidak error = pass

    async def test_multiple_runs(self):
        orch = AsyncMock()
        orch.run = AsyncMock()
        sched = SimpleScheduler(orch, interval_seconds=0.01)
        await sched.start()
        await asyncio.sleep(0.05)
        await sched.stop()
        assert orch.run.call_count >= 1

    async def test_deterministic_run_once(self):
        orch1 = AsyncMock()
        orch1.run = AsyncMock(return_value="result")
        orch2 = AsyncMock()
        orch2.run = AsyncMock(return_value="result")
        s1 = SimpleScheduler(orch1)
        s2 = SimpleScheduler(orch2)
        r1 = await s1.run_once("BTC")
        r2 = await s2.run_once("BTC")
        assert r1 == r2