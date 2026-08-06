"""Binance Balance Provider."""

from datetime import UTC, datetime

from src.core.models.exchange_account import ExchangeAccountSnapshot
from src.exchange.adapters.binance.client import BinanceClient
from src.exchange.adapters.binance.exceptions import BinanceAPIError


class BinanceBalanceProvider:
    def __init__(self, client: BinanceClient) -> None:
        self.client = client

    async def get_account_snapshot(self) -> ExchangeAccountSnapshot:
        try:
            account = await self.client.get_account()
            return ExchangeAccountSnapshot(
                asset="USDT",
                wallet_balance=float(account.get("totalWalletBalance", 0)),
                available_balance=float(account.get("availableBalance", 0)),
                unrealized_pnl=float(account.get("totalUnrealizedProfit", 0)),
                timestamp=datetime.now(UTC),
            )
        except (BinanceAPIError, Exception):
            return ExchangeAccountSnapshot(
                asset="USDT",
                wallet_balance=0.0,
                available_balance=0.0,
                unrealized_pnl=0.0,
                timestamp=datetime.now(UTC),
            )