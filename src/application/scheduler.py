"""Scheduler — trigger pipeline secara berkala."""

import asyncio
from abc import ABC, abstractmethod


class BaseScheduler(ABC):
    @abstractmethod
    async def start(self) -> None:
        ...

    @abstractmethod
    async def stop(self) -> None:
        ...


class SimpleScheduler(BaseScheduler):
    def __init__(self, pipeline_runner, interval_seconds: int = 14400):
        self.runner = pipeline_runner
        self.interval = interval_seconds
        self._running = False
        self._task = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    async def run_once(self, symbol: str, timeframe: str = "4h"):
        return await self.runner.run(symbol, timeframe)

    async def _loop(self) -> None:
        while self._running:
            try:
                await self.runner.run("BTC", "4h")
            except Exception:
                pass
            await asyncio.sleep(self.interval)