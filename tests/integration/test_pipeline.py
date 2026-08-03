"""Integration test: Collector → Normalizer → NormalizedAsset."""

import json
from pathlib import Path

import pytest

from src.core.models.candle import Candle
from src.core.models.normalized_asset import (
    NormalizedAsset,
    RawBinanceData,
    RawCoinGeckoData,
    RawFearGreedData,
    RawNewsData,
)
from src.normalizer.asset_normalizer import AssetNormalizer

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def mock_raw_data():
    """Load full mocked collector output."""
    with open(FIXTURES / "normalized_asset.json") as f:
        data = json.load(f)

    data["binance"] = RawBinanceData(**data["binance"])
    data["coingecko"] = RawCoinGeckoData(**data["coingecko"])
    data["fear_greed"] = RawFearGreedData(**data["fear_greed"])
    data["news"] = RawNewsData(**data["news"])

    return data


class TestPipeline:
    """Integration tests untuk Collector → Normalizer flow."""

    def test_full_pipeline_normalize(self, mock_raw_data):
        """Mock data → normalize → valid NormalizedAsset dengan semua field."""
        normalizer = AssetNormalizer()
        result = normalizer.normalize(mock_raw_data)

        assert isinstance(result, NormalizedAsset)
        assert result.symbol == "BTC"
        assert result.price == 47500.00
        assert result.volume_24h == 28000000000.0
        assert result.data_quality_score == 1.0
        assert result.timestamp is not None

    def test_pipeline_candles_are_candle_objects(self, mock_raw_data):
        """candles_4h dan candles_1h harus list[Candle], bukan raw list."""
        normalizer = AssetNormalizer()
        result = normalizer.normalize(mock_raw_data)

        assert len(result.candles_4h) == 25
        assert len(result.candles_1h) == 1

        for candle in result.candles_4h:
            assert isinstance(candle, Candle)

        for candle in result.candles_1h:
            assert isinstance(candle, Candle)

        # Verifikasi isi candle pertama dan terakhir
        first_candle = result.candles_4h[0]
        assert first_candle.open == 45000.00
        assert first_candle.close == 44900.00
        assert first_candle.volume == 1250.5

        last_candle = result.candles_4h[-1]
        assert last_candle.open == 47400.00
        assert last_candle.close == 47350.00