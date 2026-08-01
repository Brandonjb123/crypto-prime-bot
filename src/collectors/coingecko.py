"""CoinGecko collector — market data, ranking, volume."""

from loguru import logger

from src.collectors.base_http_client import BaseHTTPClient
from src.core.exceptions.collector_exceptions import DataQualityError
from src.core.interfaces.base_collector import BaseCollector
from src.core.models.normalized_asset import RawCoinGeckoData

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

SYMBOL_MAP: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "SOL": "solana",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "POL": "polygon-ecosystem-token",
    "TRX": "tron",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "ATOM": "cosmos",
    "LTC": "litecoin",
    "FIL": "filecoin",
    "APT": "aptos",
    "ARB": "arbitrum",
    "OP": "optimism",
    "NEAR": "near",
    "INJ": "injective-protocol",
    "SUI": "sui",
    "PEPE": "pepe",
    "HBAR": "hedera-hashgraph",
    "CRO": "crypto-com-chain",
    "MNT": "mantle",
    "XDC": "xdce-crowd-sale",
    "QNT": "quant-network",
    "PAXG": "pax-gold",
    "HTX": "huobi-token",
}


class CoinGeckoCollector(BaseCollector):
    """Collect market cap, volume, price change dari CoinGecko."""

    def __init__(self) -> None:
        self.client = BaseHTTPClient(COINGECKO_BASE_URL, timeout=15.0)

    async def fetch(self, symbol: str) -> RawCoinGeckoData:
        """Fetch market data untuk satu symbol."""
        coin_id = SYMBOL_MAP.get(symbol.upper())
        if not coin_id:
            raise DataQualityError(f"Unknown symbol: {symbol}")

        logger.debug(f"Fetching CoinGecko data for {symbol} ({coin_id})")

        data = await self.client.get(
            f"/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "community_data": "false",
                "developer_data": "false",
            },
        )

        market = data.get("market_data", {})
        return RawCoinGeckoData(
            symbol=symbol,
            coin_id=coin_id,
            current_price=market.get("current_price", {}).get("usd", 0.0),
            market_cap=market.get("market_cap", {}).get("usd", 0.0),
            total_volume=market.get("total_volume", {}).get("usd", 0.0),
            price_change_24h=market.get("price_change_percentage_24h", 0.0),
            price_change_7d=market.get("price_change_percentage_7d", 0.0),
        )

    async def health_check(self) -> bool:
        """Ping CoinGecko API."""
        try:
            await self.client.get("/ping")
            return True
        except Exception:
            return False