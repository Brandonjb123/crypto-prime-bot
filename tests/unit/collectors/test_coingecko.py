"""Unit tests untuk CoinGeckoCollector."""

import json
from pathlib import Path

import pytest

from src.collectors.coingecko import CoinGeckoCollector
from src.core.exceptions.collector_exceptions import DataQualityError
from src.core.models.normalized_asset import RawCoinGeckoData

FIXTURES = Path(__file__).parent.parent.parent / "fixtures"


@pytest.fixture
def mock_coingecko():
    with open(FIXTURES / "coingecko_market.json") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_coingecko_fetch_success(monkeypatch, mock_coingecko):
    """Test fetch sukses return RawCoinGeckoData."""

    async def mock_get(self, endpoint, params=None):
        return mock_coingecko

    monkeypatch.setattr("src.collectors.base_http_client.BaseHTTPClient.get", mock_get)

    collector = CoinGeckoCollector()
    result = await collector.fetch("BTC")

    assert isinstance(result, RawCoinGeckoData)
    assert result.symbol == "BTC"
    assert result.coin_id == "bitcoin"
    assert result.current_price == 45000.00
    assert result.market_cap == 850000000000
    assert result.total_volume == 28000000000
    assert result.price_change_24h == 2.5
    assert result.price_change_7d == -1.2


@pytest.mark.asyncio
async def test_coingecko_fetch_unknown_symbol(monkeypatch):
    """Test fetch dengan simbol tidak dikenal."""

    collector = CoinGeckoCollector()
    with pytest.raises(DataQualityError):
        await collector.fetch("XXXXX")


@pytest.mark.asyncio
async def test_coingecko_health_check(monkeypatch):
    """Test health check CoinGecko."""

    async def mock_get(self, endpoint, params=None):
        return {"gecko_says": "pong"}

    monkeypatch.setattr("src.collectors.base_http_client.BaseHTTPClient.get", mock_get)

    collector = CoinGeckoCollector()
    assert await collector.health_check() is True
