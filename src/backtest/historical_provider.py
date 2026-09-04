"""Historical Price Provider — menggunakan candle terakhir sebagai current price."""

from src.core.models.backtest import HistoricalCandle


class HistoricalPriceProvider:
    def __init__(self) -> None:
        self._candles: dict[str, float] = {}

    def load(self, candles: list[HistoricalCandle]) -> None:
        """Load historical candles; price = close dari candle terbaru per symbol."""
        for c in candles:
            self._candles[c.symbol] = c.close

    def get_price(self, symbol: str) -> float | None:
        """Return harga terbaru."""
        return self._candles.get(symbol)

    def update_price(self, symbol: str, price: float) -> None:
        """Set harga manual (untuk replay)."""
        self._candles[symbol] = price
