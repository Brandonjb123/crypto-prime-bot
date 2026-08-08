"""Binance Market Data Collector — mengambil OHLCV dan harga terkini."""

import asyncio
from datetime import UTC, datetime

import httpx

from src.core.models.market_snapshot import MarketSnapshot
from src.logging.logger import get_logger

logger = get_logger("binance_collector")

BINANCE_BASE_URL = "https://api.binance.com/api/v3"
MAX_RETRIES = 3
RETRY_DELAY = 1.0
TIMEOUT = 10.0


class BinanceCollector:
    def __init__(self):
        self.base_url = BINANCE_BASE_URL

    async def collect(self, symbol: str, timeframe: str = "4h") -> MarketSnapshot:
        symbol_upper = symbol.upper()
        binance_symbol = f"{symbol_upper}USDT"

        logger.info(f"Fetching Binance data for {binance_symbol} ({timeframe})")

        # Ambil klines (OHLCV)
        klines = await self._get_klines(binance_symbol, timeframe)

        # Ambil harga terkini (ticker)
        current_price = await self._get_current_price(binance_symbol)

        logger.info(f"Market snapshot created for {symbol_upper}")

        return MarketSnapshot(
            symbol=symbol_upper,
            timeframe=timeframe,
            current_price=current_price,
            candles=klines,
            market_cap=0.0,  # CoinGecko nanti
            volume_24h=sum(float(k[5]) for k in klines[-24:]) if klines else 0.0,
            change_24h=0.0,  # CoinGecko nanti
            timestamp=datetime.now(UTC),
        )

    async def _get_klines(self, symbol: str, interval: str) -> list:
        """Ambil klines dengan retry."""
        url = f"{self.base_url}/klines"
        params = {"symbol": symbol, "interval": interval, "limit": 50}

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    return resp.json()
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY * attempt)
                else:
                    logger.error(f"All retries exhausted for {symbol} klines")
                    raise

    async def _get_current_price(self, symbol: str) -> float:
        """Ambil harga terkini via ticker."""
        url = f"{self.base_url}/ticker/price"
        params = {"symbol": symbol}

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    return float(data["price"])
            except Exception as e:
                logger.warning(f"Price attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY * attempt)
                else:
                    logger.error(f"All retries exhausted for {symbol} price")
                    raise