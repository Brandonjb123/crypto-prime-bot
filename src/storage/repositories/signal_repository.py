"""Signal Repository interface — append-only signal history."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

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

    @abstractmethod
    def get_lifecycle_states(
        self, signal_ids: list[UUID]
    ) -> dict[UUID, str]:
        """Bulk read lifecycle state for signal IDs.

        Returns {signal_id: 'ACTIVE'|'EXPIRED'} for IDs that have a
        signal_lifecycle row. Missing keys = no lifecycle row (caller
        interprets as LEGACY).

        Raises on query failure (caller must catch and fall back to
        UNKNOWN — never LEGACY).
        """
        ...    