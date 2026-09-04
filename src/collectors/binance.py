"""Binance Public API collector — no auth required."""

from loguru import logger

from src.collectors.base_http_client import BaseHTTPClient
from src.core.exceptions.collector_exceptions import DataQualityError
from src.core.interfaces.base_collector import BaseCollector
from src.core.models.normalized_asset import RawBinanceData

BINANCE_BASE_URL = "https://fapi.binance.com"  # Futures endpoint


class BinanceCollector(BaseCollector):
    """Collect OHLCV, Funding Rate, Open Interest, Long/Short Ratio."""

    def __init__(self) -> None:
        self.client = BaseHTTPClient(BINANCE_BASE_URL)

    async def fetch(self, symbol: str) -> RawBinanceData:
        """Fetch semua data futures untuk satu symbol."""
        binance_symbol = symbol.replace("/", "").upper() + "T"

        logger.debug(f"Fetching Binance data for {binance_symbol}")

        try:
            # OHLCV 4H — 50 candles
            candles_4h = await self.client.get(
                "/fapi/v1/klines",
                params={"symbol": binance_symbol, "interval": "4h", "limit": 50},
            )

            # OHLCV 1H — 50 candles
            candles_1h = await self.client.get(
                "/fapi/v1/klines",
                params={"symbol": binance_symbol, "interval": "1h", "limit": 50},
            )

            # Funding Rate
            funding = await self.client.get(
                "/fapi/v1/fundingRate",
                params={"symbol": binance_symbol, "limit": 1},
            )

            # Open Interest
            open_interest = await self.client.get(
                "/fapi/v1/openInterest",
                params={"symbol": binance_symbol},
            )

            # Long/Short Ratio
            ls_ratio = await self.client.get(
                "/futures/data/globalLongShortAccountRatio",
                params={"symbol": binance_symbol, "period": "4h", "limit": 1},
            )

        except Exception as e:
            logger.error(f"Binance fetch failed for {symbol}: {e}")
            raise

        if not candles_4h or len(candles_4h) < 20:
            raise DataQualityError(f"Insufficient candle data for {symbol}")

        return RawBinanceData(
            symbol=symbol,
            candles_4h=candles_4h,
            candles_1h=candles_1h,
            funding_rate=float(funding[0]["fundingRate"]) if funding else 0.0,
            open_interest=float(open_interest.get("openInterest", 0)),
            long_short_ratio=float(ls_ratio[0]["longShortRatio"]) if ls_ratio else 1.0,
        )

    async def health_check(self) -> bool:
        """Ping Binance API."""
        try:
            await self.client.get("/fapi/v1/ping")
            return True
        except Exception:
            return False
