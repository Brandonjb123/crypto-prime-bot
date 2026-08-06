"""Binance Position Provider."""

from src.core.models.position import Position
from src.exchange.adapters.binance.binance_mapper import map_position
from src.exchange.adapters.binance.client import BinanceClient


class BinancePositionProvider:
    def __init__(self, client: BinanceClient) -> None:
        self.client = client

    async def get_exchange_positions(self) -> list[Position]:
        try:
            # Get all open positions from Binance
            account = await self.client.get_account()
            positions = account.get("positions", [])
            result = []
            for pos in positions:
                mapped = map_position(pos)
                if mapped is not None:
                    result.append(mapped)
            return result
        except Exception:
            return []