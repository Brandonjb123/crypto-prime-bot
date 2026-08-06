"""Unit tests untuk BinanceBalanceProvider."""

from unittest.mock import AsyncMock, MagicMock

from src.core.models.exchange_account import ExchangeAccountSnapshot
from src.exchange.adapters.binance.binance_balance_provider import BinanceBalanceProvider
from src.exchange.adapters.binance.client import BinanceClient


class TestBinanceBalanceProvider:
    async def test_account_success(self):
        client = MagicMock(spec=BinanceClient)
        client.get_account = AsyncMock(return_value={
            "totalWalletBalance": "10000.00",
            "availableBalance": "9500.00",
            "totalUnrealizedProfit": "200.00",
        })
        provider = BinanceBalanceProvider(client)
        snapshot = await provider.get_account_snapshot()
        assert isinstance(snapshot, ExchangeAccountSnapshot)
        assert snapshot.wallet_balance == 10000.0
        assert snapshot.available_balance == 9500.0
        assert snapshot.unrealized_pnl == 200.0

    async def test_api_failure(self):
        client = MagicMock(spec=BinanceClient)
        client.get_account = AsyncMock(side_effect=Exception("API down"))
        provider = BinanceBalanceProvider(client)
        snapshot = await provider.get_account_snapshot()
        assert snapshot.wallet_balance == 0.0
        assert snapshot.available_balance == 0.0
        assert snapshot.unrealized_pnl == 0.0