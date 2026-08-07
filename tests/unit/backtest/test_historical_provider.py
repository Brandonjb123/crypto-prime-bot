from datetime import UTC, datetime

from src.backtest.historical_provider import HistoricalPriceProvider
from src.core.models.backtest import HistoricalCandle


def make_candle(close):
    return HistoricalCandle(
        timestamp=datetime.now(UTC),
        symbol="BTCUSDT",
        timeframe="4h",
        open=close - 1,
        high=close + 2,
        low=close - 2,
        close=close,
        volume=100.0,
    )


class TestHistoricalPriceProvider:
    def test_latest_price(self):
        provider = HistoricalPriceProvider()
        provider.load([make_candle(100.0), make_candle(110.0)])
        assert provider.get_price("BTCUSDT") == 110.0

    def test_unknown_symbol(self):
        provider = HistoricalPriceProvider()
        assert provider.get_price("ETHUSDT") is None

    def test_overwrite(self):
        provider = HistoricalPriceProvider()
        provider.update_price("BTCUSDT", 200.0)
        assert provider.get_price("BTCUSDT") == 200.0
