"""Unit tests untuk AssetNormalizer."""

import json
from pathlib import Path

import pytest

from src.core.exceptions.collector_exceptions import InsufficientDataError
from src.core.models.candle import Candle
from src.core.models.normalized_asset import (
    NormalizedAsset,
    RawBinanceData,
    RawCoinGeckoData,
    RawFearGreedData,
    RawNewsData,
)
from src.normalizer.asset_normalizer import AssetNormalizer

FIXTURES = Path(__file__).parent.parent.parent / "fixtures"


@pytest.fixture
def sample_raw_data():
    with open(FIXTURES / "normalized_asset.json") as f:
        data = json.load(f)

    if data.get("binance"):
        data["binance"] = RawBinanceData(**data["binance"])
    if data.get("coingecko"):
        data["coingecko"] = RawCoinGeckoData(**data["coingecko"])
    if data.get("fear_greed"):
        data["fear_greed"] = RawFearGreedData(**data["fear_greed"])
    if data.get("news"):
        data["news"] = RawNewsData(**data["news"])

    return data


class TestAssetNormalizer:

    def test_normalize_success_all_fields(self, sample_raw_data):
        normalizer = AssetNormalizer()
        result = normalizer.normalize(sample_raw_data)

        assert isinstance(result, NormalizedAsset)
        assert result.symbol == "BTC"
        assert result.price == 47500.00
        assert result.volume_24h == 28000000000.0
        assert result.market_cap == 900000000000.0
        assert result.price_change_24h == 2.5
        assert result.price_change_7d == -1.2
        assert result.funding_rate == 0.0001
        assert result.open_interest == 15000000000.0
        assert result.long_short_ratio == 1.25
        assert result.fear_greed_value == 25
        assert result.fear_greed_classification == "Extreme Fear"
        assert len(result.news_headlines) == 2
        assert len(result.candles_4h) == 25
        assert len(result.candles_1h) == 1
        assert result.data_quality_score == 1.0
        assert result.timestamp is not None

        # Verify candles are Candle objects, not raw lists
        assert isinstance(result.candles_4h[0], Candle)
        assert result.candles_4h[0].open == 45000.00
        assert result.candles_4h[-1].close == 47350.00
        assert isinstance(result.candles_1h[0], Candle)
        assert result.candles_1h[0].open == 47500.00

    def test_volume_spike_ratio_calculation(self, sample_raw_data):
        normalizer = AssetNormalizer()
        result = normalizer.normalize(sample_raw_data)

        # Perhitungan dari raw klines (index 5 = volume)
        raw_candles = sample_raw_data["binance"].candles_4h
        current_volume = float(raw_candles[-1][5])
        prev_volumes = [float(c[5]) for c in raw_candles[-21:-1]]
        expected_avg = sum(prev_volumes) / 20
        expected_ratio = round(current_volume / expected_avg, 4)

        assert result.volume_spike_ratio == expected_ratio

    def test_volume_spike_ratio_insufficient_candles(self, sample_raw_data):
        sample_raw_data["binance"].candles_4h = sample_raw_data["binance"].candles_4h[:5]

        normalizer = AssetNormalizer()
        result = normalizer.normalize(sample_raw_data)
        assert result.volume_spike_ratio == 1.0

    def test_insufficient_data_quality(self, sample_raw_data):
        sample_raw_data["data_quality_score"] = 0.50

        normalizer = AssetNormalizer()
        with pytest.raises(InsufficientDataError):
            normalizer.normalize(sample_raw_data)

    def test_missing_binance_triggers_insufficient(self, sample_raw_data):
        sample_raw_data["binance"] = None
        sample_raw_data["data_quality_score"] = 0.35

        normalizer = AssetNormalizer()
        with pytest.raises(InsufficientDataError):
            normalizer.normalize(sample_raw_data)

    def test_null_non_critical_sources_use_fallback(self, sample_raw_data):
        sample_raw_data["fear_greed"] = None
        sample_raw_data["news"] = None

        normalizer = AssetNormalizer()
        result = normalizer.normalize(sample_raw_data)

        assert result.fear_greed_value == 0
        assert result.fear_greed_classification == "unknown"
        assert result.news_headlines == []

    def test_serialize_to_json(self, sample_raw_data):
        normalizer = AssetNormalizer()
        result = normalizer.normalize(sample_raw_data)

        json_str = result.model_dump_json()
        assert isinstance(json_str, str)

        parsed = json.loads(json_str)
        assert parsed["symbol"] == "BTC"
        assert parsed["price"] == 47500.00
        assert parsed["fear_greed_value"] == 25
        # Candle objects should be serialized as dicts
        assert isinstance(parsed["candles_4h"], list)
        assert isinstance(parsed["candles_4h"][0], dict)
        assert parsed["candles_4h"][0]["open"] == 45000.00