"""In-memory historical data provider."""

from src.backtesting.historical_data_provider import HistoricalDataProvider
from src.core.models.market_snapshot import MarketSnapshot


class InMemoryHistoricalDataProvider(HistoricalDataProvider):
    def __init__(self, snapshots: list[MarketSnapshot]):
        self.snapshots = sorted(snapshots, key=lambda s: s.timestamp)

    def get_data(self, symbol: str, timeframe: str) -> list[MarketSnapshot]:
        return [s for s in self.snapshots if s.symbol == symbol and s.timeframe == timeframe]