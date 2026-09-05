from unittest.mock import AsyncMock

import pytest

from src.market.in_memory_price_provider import InMemoryPriceProvider
from src.market.price_refresh_service import PriceRefreshService


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


@pytest.mark.asyncio
async def test_refresh_updates_single_symbol():
    provider = InMemoryPriceProvider()
    client = AsyncMock()
    client.get = AsyncMock(return_value=FakeResponse({"price": "80000.0"}))

    service = PriceRefreshService(provider, symbols=["BTC"], http_client=client)
    await service.refresh_once()

    assert provider.get_price("BTC") == 80000.0


@pytest.mark.asyncio
async def test_refresh_updates_multiple_symbols():
    provider = InMemoryPriceProvider()

    async def fake_get(url, *args, **kwargs):
        if "BTCUSDT" in url:
            return FakeResponse({"price": "80000.0"})
        if "ETHUSDT" in url:
            return FakeResponse({"price": "2500.0"})
        return FakeResponse({"price": "0"})

    client = AsyncMock()
    client.get = AsyncMock(side_effect=fake_get)

    service = PriceRefreshService(provider, symbols=["BTC", "ETH"], http_client=client)
    await service.refresh_once()

    assert provider.get_price("BTC") == 80000.0
    assert provider.get_price("ETH") == 2500.0


@pytest.mark.asyncio
async def test_refresh_api_failure_does_not_crash():
    provider = InMemoryPriceProvider()
    client = AsyncMock()
    client.get = AsyncMock(side_effect=Exception("network error"))

    service = PriceRefreshService(provider, symbols=["BTC"], http_client=client)
    # Tidak boleh raise
    await service.refresh_once()

    # Harga tetap None karena tidak ter-update
    assert provider.get_price("BTC") is None