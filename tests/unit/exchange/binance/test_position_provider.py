"""Unit tests untuk BinancePositionProvider."""

from unittest.mock import AsyncMock, MagicMock

from src.core.models.position import Position
from src.exchange.adapters.binance.binance_position_provider import BinancePositionProvider
from src.exchange.adapters.binance.client import BinanceClient


class TestBinancePositionProvider:
    async def test_parse_positions(self):
        client = MagicMock(spec=BinanceClient)
        client.get_account = AsyncMock(return_value={
            "positions": [
                {"positionAmt": "0.5", "entryPrice": "50000.0", "symbol": "BTCUSDT", "unrealizedProfit": "100.0"},
                {"positionAmt": "-0.2", "entryPrice": "3000.0", "symbol": "ETHUSDT", "unrealizedProfit": "-50.0"},
                {"positionAmt": "0", "entryPrice": "0", "symbol": "SOLUSDT", "unrealizedProfit": "0"},
            ]
        })
        provider = BinancePositionProvider(client)
        positions = await provider.get_exchange_positions()
        assert len(positions) == 2
        assert all(isinstance(p, Position) for p in positions)

    async def test_empty_positions(self):
        client = MagicMock(spec=BinanceClient)
        client.get_account = AsyncMock(return_value={"positions": []})
        provider = BinancePositionProvider(client)
        positions = await provider.get_exchange_positions()
        assert len(positions) == 0