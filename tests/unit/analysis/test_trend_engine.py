"""Unit tests untuk TrendEngine."""

from datetime import UTC, datetime

from src.analysis.trend_engine import TrendEngine
from src.core.models.analysis import TechnicalAnalysis
from src.core.types.enums import TrendDirection


def _make_ta(ema20, ema50, rsi14, atr14):
    """Helper: buat TechnicalAnalysis dengan timestamp."""
    return TechnicalAnalysis(
        ema20=ema20,
        ema50=ema50,
        rsi14=rsi14,
        atr14=atr14,
        timestamp=datetime.now(UTC),
    )


class TestTrendEngine:
    def test_bullish(self):
        engine = TrendEngine()
        ta = _make_ta(50000.0, 48000.0, 60.0, 500.0)
        result = engine.analyze(ta, price=51000.0)
        assert result == TrendDirection.BULLISH

    def test_bearish(self):
        engine = TrendEngine()
        ta = _make_ta(45000.0, 47000.0, 40.0, 500.0)
        result = engine.analyze(ta, price=44000.0)
        assert result == TrendDirection.BEARISH

    def test_sideways_price_between(self):
        engine = TrendEngine()
        ta = _make_ta(50000.0, 48000.0, 55.0, 500.0)
        result = engine.analyze(ta, price=49000.0)
        assert result == TrendDirection.SIDEWAYS

    def test_sideways_ema_none(self):
        engine = TrendEngine()
        ta = _make_ta(None, None, None, None)
        result = engine.analyze(ta, price=50000.0)
        assert result == TrendDirection.SIDEWAYS

    def test_sideways_mixed(self):
        engine = TrendEngine()
        ta = _make_ta(46000.0, 48000.0, 50.0, 500.0)
        result = engine.analyze(ta, price=47000.0)
        assert result == TrendDirection.SIDEWAYS
