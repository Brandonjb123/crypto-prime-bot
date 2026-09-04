"""Unit tests untuk FearGreedCollector."""

import json
from pathlib import Path

import pytest

from src.collectors.fear_greed import FearGreedCollector
from src.core.models.normalized_asset import RawFearGreedData

FIXTURES = Path(__file__).parent.parent.parent / "fixtures"


@pytest.fixture
def mock_fear_greed():
    with open(FIXTURES / "fear_greed.json") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_fear_greed_fetch_success(monkeypatch, mock_fear_greed):
    """Test fetch sukses return RawFearGreedData."""

    async def mock_get(self, endpoint, params=None):
        return mock_fear_greed

    monkeypatch.setattr("src.collectors.base_http_client.BaseHTTPClient.get", mock_get)

    collector = FearGreedCollector()
    result = await collector.fetch()

    assert isinstance(result, RawFearGreedData)
    assert result.symbol == "market"
    assert result.value == 25
    assert result.classification == "Extreme Fear"
    assert result.timestamp == 1700000000


@pytest.mark.asyncio
async def test_fear_greed_health_check(monkeypatch):
    """Test health check Fear & Greed."""

    async def mock_get(self, endpoint, params=None):
        return {"data": [{"value": "50"}]}

    monkeypatch.setattr("src.collectors.base_http_client.BaseHTTPClient.get", mock_get)

    collector = FearGreedCollector()
    assert await collector.health_check() is True
