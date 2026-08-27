"""Scheduler — trigger pipeline secara berkala untuk multi-asset."""

import asyncio
from abc import ABC, abstractmethod

# Universe simulasi paper trading
DEFAULT_SYMBOLS = [
    "BTC",
    "ETH",
    "BNB",
    "SOL",
    "XRP",
    "DOGE",
    "ADA",
    "AVAX",
    "LINK",
]


class BaseScheduler(ABC):
    @abstractmethod
    async def start(self) -> None:
        ...

    @abstractmethod
    async def stop(self) -> None:
        ...


class SimpleScheduler(BaseScheduler):
    def __init__(
        self,
        pipeline_runner,
        interval_seconds: int = 14400,
        symbols: list[str] | None = None,
    ):
        self.runner = pipeline_runner
        self.interval = interval_seconds
        self.symbols = symbols or DEFAULT_SYMBOLS
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
            for symbol in self.symbols:
                if not self._running:
                    break
                try:
                    await self.runner.run(symbol, "4h")
                except Exception:
                    pass
            await asyncio.sleep(self.interval)