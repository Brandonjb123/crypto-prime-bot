"""Unit tests untuk VolatilityEngine."""

from datetime import UTC, datetime

from src.analysis.volatility_engine import VolatilityEngine
from src.core.models.analysis import TechnicalAnalysis
from src.core.models.market_intelligence import VolatilityAnalysis


class TestVolatilityEngine:
    def test_high_risk(self):
        """ATR >= 3% dari harga → HIGH risk."""
        engine = VolatilityEngine()
        ta = TechnicalAnalysis(
            ema20=50000.0, ema50=48000.0, rsi14=60.0, atr14=2000.0,
            timestamp=datetime.now(UTC),
        )
        result = engine.analyze(ta, price=50000.0)

        assert isinstance(result, VolatilityAnalysis)
        assert result.atr == 2000.0
        assert result.atr_normalized == 4.0  # 2000/50000 * 100
        assert result.risk_level == "HIGH"
        assert result.confidence_score == 0.5  # high vol = less confidence

    def test_low_risk(self):
        """ATR < 1% dari harga → LOW risk."""
        engine = VolatilityEngine()
        ta = TechnicalAnalysis(
            ema20=50000.0, ema50=48000.0, rsi14=60.0, atr14=200.0,
            timestamp=datetime.now(UTC),
        )
        result = engine.analyze(ta, price=50000.0)

        assert result.atr == 200.0
        assert result.atr_normalized == 0.4  # 200/50000 * 100
        assert result.risk_level == "LOW"
        assert result.confidence_score == 0.7

    def test_medium_risk(self):
        """ATR antara 1% - 3% → MEDIUM risk (ideal trading)."""
        engine = VolatilityEngine()
        ta = TechnicalAnalysis(
            ema20=50000.0, ema50=48000.0, rsi14=60.0, atr14=1000.0,
            timestamp=datetime.now(UTC),
        )
        result = engine.analyze(ta, price=50000.0)

        assert result.atr == 1000.0
        assert result.atr_normalized == 2.0  # 1000/50000 * 100
        assert result.risk_level == "MEDIUM"
        assert result.confidence_score == 1.0  # ideal for trading

    def test_atr_none(self):
        """ATR None → fallback 0, risk LOW."""
        engine = VolatilityEngine()
        ta = TechnicalAnalysis(
            ema20=50000.0, ema50=48000.0, rsi14=60.0, atr14=None,
            timestamp=datetime.now(UTC),
        )
        result = engine.analyze(ta, price=50000.0)

        assert result.atr == 0.0
        assert result.atr_normalized == 0.0
        assert result.risk_level == "LOW"

    def test_confidence_range(self):
        """Confidence score harus antara 0.0-1.0."""
        engine = VolatilityEngine()
        for atr in [100.0, 500.0, 1000.0, 2000.0, 5000.0]:
            ta = TechnicalAnalysis(
                ema20=50000.0, ema50=48000.0, rsi14=60.0, atr14=atr,
                timestamp=datetime.now(UTC),
            )
            result = engine.analyze(ta, price=50000.0)
            assert 0.0 <= result.confidence_score <= 1.0