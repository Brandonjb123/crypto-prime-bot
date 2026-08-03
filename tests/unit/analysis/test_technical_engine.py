"""Unit tests untuk TechnicalAnalysisEngine."""

from datetime import UTC, datetime, timedelta

from src.analysis.technical_engine import TechnicalAnalysisEngine
from src.core.models.analysis import TechnicalAnalysis
from src.core.models.candle import Candle
from src.core.models.normalized_asset import NormalizedAsset


def make_asset(candle_count: int, base_price: float = 100.0) -> NormalizedAsset:
    """Helper: buat NormalizedAsset dengan n candle (uptrend)."""
    candles = []
    for i in range(candle_count):
        ts = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC) + timedelta(hours=4 * i)
        close = base_price + i * 0.5
        candles.append(
            Candle(
                timestamp=ts,
                open=close - 0.3,
                high=close + 0.4,
                low=close - 0.4,
                close=close,
                volume=1000.0,
            )
        )
    return NormalizedAsset(
        symbol="BTC",
        price=base_price + candle_count * 0.5,
        volume_24h=28000000000.0,
        volume_spike_ratio=1.0,
        market_cap=900000000000.0,
        price_change_24h=2.5,
        price_change_7d=-1.2,
        funding_rate=0.0001,
        open_interest=15000000000.0,
        long_short_ratio=1.25,
        fear_greed_value=25,
        fear_greed_classification="Extreme Fear",
        news_headlines=[],
        candles_4h=candles,
        candles_1h=[],
        data_quality_score=1.0,
        timestamp=datetime.now(UTC),
    )


class TestTechnicalAnalysisEngine:
    def test_analyze_sufficient_candles(self):
        """50+ candle → semua field terisi."""
        engine = TechnicalAnalysisEngine()
        asset = make_asset(55, base_price=45000.0)
        result = engine.analyze(asset)

        assert isinstance(result, TechnicalAnalysis)
        assert result.ema20 is not None
        assert result.ema50 is not None
        assert result.rsi14 is not None
        assert result.atr14 is not None
        assert result.timestamp is not None

    def test_analyze_insufficient_candles(self):
        """< 50 candle → semua field None."""
        engine = TechnicalAnalysisEngine()
        asset = make_asset(30, base_price=45000.0)
        result = engine.analyze(asset)

        assert result.ema20 is None
        assert result.ema50 is None
        assert result.rsi14 is None
        assert result.atr14 is None

    def test_analyze_rsi_range(self):
        """RSI harus antara 0–100."""
        engine = TechnicalAnalysisEngine()
        asset = make_asset(55, base_price=45000.0)
        result = engine.analyze(asset)
        assert 0 <= result.rsi14 <= 100

    def test_analyze_atr_positive(self):
        """ATR harus positif."""
        engine = TechnicalAnalysisEngine()
        asset = make_asset(55, base_price=45000.0)
        result = engine.analyze(asset)
        assert result.atr14 > 0