"""Unit tests untuk AssetNormalizer."""

import json
from pathlib import Path

import pytest

from src.core.exceptions.collector_exceptions import InsufficientDataError
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

    # Convert dicts ke Pydantic models
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
    """Test suite untuk AssetNormalizer."""

    def test_normalize_success_all_fields(self, sample_raw_data):
        """Test normalisasi sukses — semua field terisi dengan benar."""
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

    def test_volume_spike_ratio_calculation(self, sample_raw_data):
        """Test volume spike ratio dihitung dengan benar."""
        normalizer = AssetNormalizer()
        result = normalizer.normalize(sample_raw_data)

        # Ambil langsung dari fixture — 25 candle
        candles = sample_raw_data["binance"].candles_4h
        # Volume candle terakhir (index -1, kolom 5)
        current_volume = float(candles[-1][5])
        # Avg volume 20 candle sebelumnya (index -21 sampai -2)
        prev_volumes = [float(c[5]) for c in candles[-21:-1]]
        expected_avg = sum(prev_volumes) / 20
        expected_ratio = round(current_volume / expected_avg, 4)

        assert result.volume_spike_ratio == expected_ratio

    def test_volume_spike_ratio_insufficient_candles(self, sample_raw_data):
        """Test volume spike ratio = 1.0 kalau candles kurang dari 21."""
        sample_raw_data["binance"].candles_4h = sample_raw_data["binance"].candles_4h[:5]

        normalizer = AssetNormalizer()
        result = normalizer.normalize(sample_raw_data)
        assert result.volume_spike_ratio == 1.0

    def test_insufficient_data_quality(self, sample_raw_data):
        """Test raise InsufficientDataError kalau quality < 0.70."""
        sample_raw_data["data_quality_score"] = 0.50

        normalizer = AssetNormalizer()
        with pytest.raises(InsufficientDataError):
            normalizer.normalize(sample_raw_data)

    def test_missing_binance_triggers_insufficient(self, sample_raw_data):
        """Test kalau Binance None → data_quality_score di bawah threshold."""
        sample_raw_data["binance"] = None
        sample_raw_data["data_quality_score"] = 0.35  # (0 crit * 0.7) + (1 noncrit * 0.3)

        normalizer = AssetNormalizer()
        with pytest.raises(InsufficientDataError):
            normalizer.normalize(sample_raw_data)

    def test_null_non_critical_sources_use_fallback(self, sample_raw_data):
        """Test non-critical source null → pakai fallback values."""
        sample_raw_data["fear_greed"] = None
        sample_raw_data["news"] = None

        normalizer = AssetNormalizer()
        result = normalizer.normalize(sample_raw_data)

        assert result.fear_greed_value == 0
        assert result.fear_greed_classification == "unknown"
        assert result.news_headlines == []

    def test_serialize_to_json(self, sample_raw_data):
        """Test NormalizedAsset bisa di-serialize ke JSON."""
        normalizer = AssetNormalizer()
        result = normalizer.normalize(sample_raw_data)

        json_str = result.model_dump_json()
        assert isinstance(json_str, str)

        parsed = json.loads(json_str)
        assert parsed["symbol"] == "BTC"
        assert parsed["price"] == 47500.00
        assert parsed["fear_greed_value"] == 25