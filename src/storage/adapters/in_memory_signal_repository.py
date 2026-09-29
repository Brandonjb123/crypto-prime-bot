"""In-memory Signal Repository — append-only list."""

from datetime import datetime

from src.core.models.trading_signal import TradingSignal
from src.storage.repositories.signal_repository import SignalRepository


class InMemorySignalRepository(SignalRepository):
    def __init__(self) -> None:
        self._storage: list[TradingSignal] = []

    def append(self, signal: TradingSignal) -> None:
        self._storage.append(signal)

    def latest_by_symbol(self, symbol: str) -> TradingSignal | None:
        for sig in reversed(self._storage):
            if sig.symbol == symbol:
                return sig
        return None

    def history(
        self,
        symbol: str | None = None,
        since: datetime | None = None,
    ) -> list[TradingSignal]:
        results = self._storage
        if symbol is not None:
            results = [s for s in results if s.symbol == symbol]
        if since is not None:
            results = [s for s in results if s.created_at >= since]
        return sorted(results, key=lambda s: s.created_at, reverse=True)