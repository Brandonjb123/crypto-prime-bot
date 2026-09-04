"""Regression test: Telegram exception tidak mempengaruhi BinanceCollector."""

import asyncio

import httpx
import pytest
import respx
from telegram.error import Conflict

from src.collectors.binance_collector import BinanceCollector


@pytest.mark.asyncio
async def test_telegram_exception_does_not_affect_collector():
    collector = BinanceCollector()

    # Data klines: list of lists (12 elemen)
    mock_klines = [[
        1609459200000, "50000.0", "50005.0", "49995.0", "50001.0", "100.0",
        1609545599999, "5000000.0", 500, 50.0, "2500000.0", "0.0"
    ]]
    mock_price = {"price": "50000.0"}

    # Mock Binance API dengan respx
    with respx.mock:
        respx.get("https://data-api.binance.vision/api/v3/klines").mock(
            return_value=httpx.Response(200, json=mock_klines)
        )
        respx.get("https://data-api.binance.vision/api/v3/ticker/price").mock(
            return_value=httpx.Response(200, json=mock_price)
        )

        # Simulasi Telegram error di task terpisah
        async def trigger_telegram_error():
            await asyncio.sleep(0.05)
            raise Conflict("simulated conflict")

        tg_task = asyncio.create_task(trigger_telegram_error())

        # Collector harus tetap berhasil
        result = await collector.collect("BTC", "4h")
        assert result is not None
        assert result.current_price == 50000.0

        tg_task.cancel()