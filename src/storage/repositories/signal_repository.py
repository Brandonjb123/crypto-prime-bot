"""Signal Repository interface — append-only signal history."""

from abc import ABC, abstractmethod
from datetime import datetime

from src.core.models.trading_signal import TradingSignal


class SignalRepository(ABC):
    @abstractmethod
    def append(self, signal: TradingSignal) -> None:
        """Append signal ke history. Immutable, append-only."""
        ...

    @abstractmethod
    def latest_by_symbol(self, symbol: str) -> TradingSignal | None:
        """Return signal terbaru untuk symbol tertentu, atau None."""
        ...

    @abstractmethod
    def history(
        self,
        symbol: str | None = None,
        since: datetime | None = None,
    ) -> list[TradingSignal]:
        """Return history, sorted desc by created_at. Optional filter symbol & since."""
        ...