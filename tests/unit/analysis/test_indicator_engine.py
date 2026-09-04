"""Unit tests untuk IndicatorEngine."""

from datetime import UTC, datetime

from src.analysis.indicator_engine import IndicatorEngine
from src.core.models.indicator_result import IndicatorResult
from src.core.models.market_snapshot import MarketSnapshot


def _make_snapshot(candles=None):
    if candles is None:
        # 50 candle sederhana untuk perhitungan EMA/RSI/ATR
        base = 50000.0
        candles = []
        for i in range(60):
            ts = 1700000000000 + i * 3600000 * 4
            open_p = base + i * 10
            high = open_p + 20
            low = open_p - 20
            close = open_p + 5
            vol = 100.0 + i
            candles.append([ts, str(open_p), str(high), str(low), str(close), str(vol)])

    return MarketSnapshot(
        symbol="BTC",
        timeframe="4h",
        current_price=50500.0,
        candles=candles,
        timestamp=datetime.now(UTC),
    )


class TestIndicatorEngine:
    def test_calculate_returns_indicator_result(self):
        engine = IndicatorEngine()
        snapshot = _make_snapshot()
        result = engine.calculate(snapshot)

        assert isinstance(result, IndicatorResult)
        assert result.symbol == "BTC"
        assert result.ema20 is not None
        assert result.ema50 is not None
        assert result.rsi14 is not None
        assert result.atr14 is not None
        assert result.average_volume is not None
        assert result.highest_high is not None
        assert result.lowest_low is not None

    def test_empty_candles(self):
        engine = IndicatorEngine()
        snapshot = _make_snapshot([])
        result = engine.calculate(snapshot)

        assert result.ema20 is None
        assert result.average_volume is None
        assert result.highest_high is None

    def test_highest_high_lowest_low(self):
        engine = IndicatorEngine()
        snapshot = _make_snapshot()
        result = engine.calculate(snapshot)

        # Highest high harus maksimum dari semua candle.high
        expected_high = max(float(c[2]) for c in snapshot.candles)
        expected_low = min(float(c[3]) for c in snapshot.candles)
        assert result.highest_high == expected_high
        assert result.lowest_low == expected_low

    def test_average_volume(self):
        engine = IndicatorEngine()
        snapshot = _make_snapshot()
        result = engine.calculate(snapshot)

        total_vol = sum(float(c[5]) for c in snapshot.candles)
        expected_avg = round(total_vol / len(snapshot.candles), 2)
        assert result.average_volume == expected_avg