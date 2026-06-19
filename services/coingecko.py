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


async def get_market_data(coin_id: str) -> dict:
    """
    Ambil data pasar yang lebih lengkap dari CoinGecko.
    Return dict dengan: current_price, price_change_24h, price_change_7d,
    total_volume, market_cap, high_24h, low_24h.
    """
    from utils.cache import price_cache  # reuse cache yang sama
    cached = price_cache.get(f"market_{coin_id}")
    if cached:
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
        "current_price": market_data.get("current_price", {}).get("usd"),
        "price_change_24h": market_data.get("price_change_percentage_24h", 0),
        "price_change_7d": market_data.get("price_change_percentage_7d_in_currency", {}).get("usd", 0),
        "total_volume": market_data.get("total_volume", {}).get("usd"),
        "market_cap": market_data.get("market_cap", {}).get("usd"),
        "high_24h": market_data.get("high_24h", {}).get("usd"),
        "low_24h": market_data.get("low_24h", {}).get("usd"),
    }
    price_cache.set(f"market_{coin_id}", result)
    return result


STABLECOIN_SYMBOLS = {
    "USDT", "USDC", "DAI", "BUSD", "TUSD", "FDUSD",
    "USDD", "GUSD", "USDP", "PYUSD", "FRAX", "USDE",
    "EURT", "EURS"
}


async def get_top_pairs(limit: int = 100) -> list:
    """Return list top {limit} crypto by market cap."""
    from utils.cache import price_cache
    cached = price_cache.get("top_pairs")
    if cached:
        return cached[:limit]

    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()

    pairs = []
    for item in data:
        symbol = item["symbol"].upper()
        if symbol in STABLECOIN_SYMBOLS:
            continue  # Skip stablecoin
        pairs.append({
            "symbol": symbol,
            "coin_id": item["id"],
            "name": item["name"],
        })

    # Cache 1 jam
    price_cache.set("top_pairs", pairs)
    return pairs[:limit]