"""Candle Replay — iterasi candle historical secara berurutan."""

from src.core.models.backtest import HistoricalCandle


class CandleReplay:
    def replay(self, candles: list[HistoricalCandle]) -> list[HistoricalCandle]:
        """Return candles dalam urutan waktu (asumsi sudah terurut)."""
        return sorted(candles, key=lambda c: c.timestamp)
