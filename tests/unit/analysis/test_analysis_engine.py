"""Unit tests untuk AnalysisEngine."""

from datetime import UTC, datetime

from src.analysis.analysis_engine import AnalysisEngine
from src.core.models.indicator_result import IndicatorResult
from src.core.models.market_analysis import AnalysisResult


def _make_indicators(**overrides):
    defaults = dict(
        symbol="BTC",
        timeframe="4h",
        ema20=51000.0,
        ema50=50000.0,
        rsi14=65.0,
        atr14=800.0,
        average_volume=600.0,
        highest_high=52000.0,
        lowest_low=49000.0,
        timestamp=datetime.now(UTC),
    )
    defaults.update(overrides)
    return IndicatorResult(**defaults)


class TestAnalysisEngine:
    def test_trend_bullish(self):
        engine = AnalysisEngine()
        ind = _make_indicators(ema20=51000, ema50=50000)
        result = engine.analyze(ind)
        assert result.trend == "Bullish"

    def test_trend_bearish(self):
        engine = AnalysisEngine()
        ind = _make_indicators(ema20=49000, ema50=50000)
        result = engine.analyze(ind)
        assert result.trend == "Bearish"

    def test_trend_sideways(self):
        engine = AnalysisEngine()
        ind = _make_indicators(ema20=None, ema50=None)
        result = engine.analyze(ind)
        assert result.trend == "Sideways"

    def test_momentum_strong_bullish(self):
        engine = AnalysisEngine()
        ind = _make_indicators(rsi14=75)
        result = engine.analyze(ind)
        assert result.momentum == "Strong Bullish"

    def test_momentum_strong_bearish(self):
        engine = AnalysisEngine()
        ind = _make_indicators(rsi14=20)
        result = engine.analyze(ind)
        assert result.momentum == "Strong Bearish"

    def test_volatility_high(self):
        engine = AnalysisEngine()
        ind = _make_indicators(atr14=2000)
        result = engine.analyze(ind)
        assert result.volatility == "High"

    def test_volume_strength_low(self):
        engine = AnalysisEngine()
        ind = _make_indicators(average_volume=300)
        result = engine.analyze(ind)
        assert result.volume_strength == "Low"

    def test_returns_analysis_result(self):
        engine = AnalysisEngine()
        result = engine.analyze(_make_indicators())
        assert isinstance(result, AnalysisResult)
        assert result.symbol == "BTC"