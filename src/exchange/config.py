"""Binance configuration — API keys from environment."""

from pydantic import BaseModel


class BinanceConfig(BaseModel):
    api_key: str
    api_secret: str
    testnet: bool = True
    recv_window: int = 5000
