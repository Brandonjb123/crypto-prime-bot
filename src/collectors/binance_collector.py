"""Binance Market Data Collector — public endpoint, no authentication."""

import asyncio
from datetime import UTC, datetime

import httpx

from config.constants import BINANCE_MARKET_DATA_BASE_URL
from src.core.models.market_snapshot import MarketSnapshot
from src.logging.logger import get_logger

logger = get_logger("collectors.binance")

MAX_RETRIES = 3
RETRY_DELAY = 1.0
TIMEOUT = 10.0


def _should_retry(exc: Exception, attempt: int) -> bool:
    """Tentukan apakah request boleh di-retry berdasarkan jenis exception."""
    if attempt >= MAX_RETRIES:
        return False

    # Jangan retry 4xx non-transient (termasuk 451)
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        if 400 <= status_code < 500:
            return False

    # Retry timeout, network error, 5xx, dan 429
    return isinstance(
        exc,
        (
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.HTTPStatusError,
        ),
    )


class BinanceCollector:
    def __init__(self):
        # Base URL dari constants — bisa diubah via env/config
        self.base_url = BINANCE_MARKET_DATA_BASE_URL

    async def collect(self, symbol: str, timeframe: str = "4h") -> MarketSnapshot:
        symbol_upper = symbol.upper()
        binance_symbol = f"{symbol_upper}USDT"

        logger.info(f"Fetching Binance data for {binance_symbol} ({timeframe})")
        logger.debug(f"Using market data base URL: {self.base_url}")

        klines = await self._get_klines(binance_symbol, timeframe)
        current_price = await self._get_current_price(binance_symbol)

        logger.info(f"Market snapshot created for {symbol_upper}")

        return MarketSnapshot(
            symbol=symbol_upper,
            timeframe=timeframe,
            current_price=current_price,
            candles=klines,
            market_cap=0.0,
            volume_24h=sum(float(k[5]) for k in klines[-24:]) if klines else 0.0,
            change_24h=0.0,
            timestamp=datetime.now(UTC),
        )

    async def _get_klines(self, symbol: str, interval: str) -> list:
        """Ambil klines dengan retry policy yang sudah diklasifikasi."""
        url = f"{self.base_url}/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": 50}

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    return resp.json()
            except Exception as e:
                logger.warning(f"Klines attempt {attempt}/{MAX_RETRIES} failed: {type(e).__name__}: {e}")
                if not _should_retry(e, attempt):
                    logger.error(f"Klines request aborted after {attempt} attempt(s) — status: {getattr(e, 'response', None) and e.response.status_code}")
                    raise
                await asyncio.sleep(RETRY_DELAY * attempt)
        logger.error(f"All retries exhausted for {symbol} klines")
        raise RuntimeError("All klines retries exhausted")

    async def _get_current_price(self, symbol: str) -> float:
        """Ambil harga terkini via ticker dengan retry policy."""
        url = f"{self.base_url}/api/v3/ticker/price"
        params = {"symbol": symbol}

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    return float(data["price"])
            except Exception as e:
                logger.warning(f"Price attempt {attempt}/{MAX_RETRIES} failed: {type(e).__name__}: {e}")
                if not _should_retry(e, attempt):
                    logger.error(f"Price request aborted after {attempt} attempt(s)")
                    raise
                await asyncio.sleep(RETRY_DELAY * attempt)
        logger.error(f"All retries exhausted for {symbol} price")
        raise RuntimeError("All price retries exhausted")