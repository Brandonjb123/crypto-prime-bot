# services/coingecko.py
import httpx
from utils.cache import price_cache
from loguru import logger

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

async def get_price(coin_id: str) -> dict:
    cached = price_cache.get(coin_id)
    if cached:
        logger.info(f"Cache hit for {coin_id}")
        return cached

    url = f"{COINGECKO_BASE_URL}/coins/{coin_id}"
    params = {
        "localization": "false",
        "tickers": "false",
        "community_data": "false",
        "developer_data": "false",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=15.0)
        response.raise_for_status()
        data = response.json()

    market_data = data.get("market_data", {})
    result = {
        "name": data.get("name", coin_id),
        "symbol": data.get("symbol", coin_id).upper(),
        "current_price": market_data.get("current_price", {}).get("usd"),
        "market_cap": market_data.get("market_cap", {}).get("usd"),
        "total_volume": market_data.get("total_volume", {}).get("usd"),
        "price_change_percentage_24h": market_data.get("price_change_percentage_24h"),
    }

    price_cache.set(coin_id, result)
    logger.info(f"Fetched price for {coin_id}")
    return result