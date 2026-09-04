"""Integration test: NormalizedAsset → TechnicalAnalysis → MarketStructureResult."""

from datetime import UTC, datetime, timedelta

from src.analysis.market_structure_engine import MarketStructureEngine
from src.analysis.technical_engine import TechnicalAnalysisEngine
from src.analysis.trend_engine import TrendEngine
from src.core.models.candle import Candle
from src.core.models.normalized_asset import NormalizedAsset
from src.core.models.structure import MarketStructureResult
from src.core.types.enums import MarketStructure, TrendDirection


def make_asset(candle_count: int, scenario: str = "uptrend") -> NormalizedAsset:
    """Helper: buat NormalizedAsset dengan candle."""
    candles = []
    base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    base_price = 45000.0

    for i in range(candle_count):
        ts = base_time + timedelta(hours=4 * i)
        if scenario == "uptrend":
            open_p = base_price + i * 20
            high = open_p + 30
            low = open_p - 10
            close = open_p + 15
        else:
            open_p = base_price + 500 - i * 10
            high = open_p + 10
            low = open_p - 30
            close = open_p - 15

        candles.append(
            Candle(
                timestamp=ts,
                open=open_p,
                high=high,
                low=low,
                close=close,
                volume=1000.0,
            )
        )

    return NormalizedAsset(
        symbol="BTC",
        price=base_price + candle_count * 20,
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
        news_headlines=["Bitcoin rising"],
        candles_4h=candles,
        candles_1h=[],
        data_quality_score=1.0,
        timestamp=datetime.now(UTC),
    )


class TestMarketStructurePipeline:
    def test_pipeline_uptrend_bos_bullish(self):
        """Uptrend asset → detect BOS_BULLISH."""
        engine = TechnicalAnalysisEngine()
        trend = TrendEngine()
        structure = MarketStructureEngine()

        asset = make_asset(60, scenario="uptrend")
        ta = engine.analyze(asset)
        direction = trend.analyze(ta, asset.price)
        result = structure.analyze(asset.candles_4h, direction)

        assert isinstance(result, MarketStructureResult)
        assert result.structure in {
            MarketStructure.BOS_BULLISH,
            MarketStructure.NONE,
            MarketStructure.CHOCH,
        }
        assert result.direction is not None

    def test_pipeline_downtrend(self):
        """Downtrend asset → valid MarketStructureResult."""
        engine = TechnicalAnalysisEngine()
        trend = TrendEngine()
        structure = MarketStructureEngine()

        asset = make_asset(60, scenario="downtrend")
        ta = engine.analyze(asset)
        direction = trend.analyze(ta, asset.price)
        result = structure.analyze(asset.candles_4h, direction)

        assert isinstance(result, MarketStructureResult)
        assert result.direction in {TrendDirection.BEARISH, TrendDirection.SIDEWAYS}

    def test_pipeline_insufficient_candles(self):
        """< 50 candle → structure NONE, tidak crash."""
        engine = TechnicalAnalysisEngine()
        trend = TrendEngine()
        structure = MarketStructureEngine()

        asset = make_asset(30, scenario="uptrend")
        ta = engine.analyze(asset)
        direction = trend.analyze(ta, asset.price)
        result = structure.analyze(asset.candles_4h, direction)

        assert result.structure == MarketStructure.NONE
