"""Historical Data Provider abstraction."""

from abc import ABC, abstractmethod

from src.core.models.market_snapshot import MarketSnapshot


class HistoricalDataProvider(ABC):
    @abstractmethod
    def get_data(self, symbol: str, timeframe: str) -> list[MarketSnapshot]:
        """Return historical market snapshots sorted by timestamp."""
        ...