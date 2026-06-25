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


# ==================== INDIKATOR TEKNIKAL ====================

# ==================== INDIKATOR TEKNIKAL ====================

async def get_ohlc_data(coin_id: str, days: int = 14) -> list:
    cache_key = f"ohlc_{coin_id}_{days}"
    cached = price_cache.get(cache_key)
    if cached:
        return cached

    url = f"{COINGECKO_BASE_URL}/coins/{coin_id}/ohlc"
    params = {"vs_currency": "usd", "days": days}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=15.0)
            response.raise_for_status()
            data = response.json()
        price_cache.set(cache_key, data)
        return data
    except Exception as e:
        logger.warning(f"OHLC fetch gagal untuk {coin_id}: {e}")
        return []


def calculate_rsi(ohlc_data: list, period: int = 14) -> float | None:
    if len(ohlc_data) < period + 1:
        return None

    closes = [candle[4] for candle in ohlc_data]
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [abs(d) if d < 0 else 0 for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 1)


def calculate_ema(closes: list, period: int) -> float | None:
    if len(closes) < period:
        return None

    ema = sum(closes[:period]) / period
    multiplier = 2 / (period + 1)

    for close in closes[period:]:
        ema = close * multiplier + ema * (1 - multiplier)

    return round(ema, 6)


async def get_technical_indicators(coin_id: str) -> dict:
    ohlc = await get_ohlc_data(coin_id, days=14)

    if not ohlc or len(ohlc) < 51:
        return {}

    closes = [candle[4] for candle in ohlc]

    rsi = calculate_rsi(ohlc)
    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)

    recent_candles = ohlc[-4:] if len(ohlc) >= 4 else ohlc
    high_24h = max(c[2] for c in recent_candles)
    low_24h = min(c[3] for c in recent_candles)
    last_close = closes[-1]

    price_position = None
    if high_24h != low_24h:
        price_position = round(
            (last_close - low_24h) / (high_24h - low_24h) * 100, 1
        )

    ema_signal = None
    if ema20 and ema50:
        if ema20 > ema50:
            ema_signal = "Bullish (EMA20 > EMA50)"
        else:
            ema_signal = "Bearish (EMA20 < EMA50)"

    rsi_signal = None
    if rsi is not None:
        if rsi > 70:
            rsi_signal = f"Overbought ({rsi})"
        elif rsi < 30:
            rsi_signal = f"Oversold ({rsi})"
        else:
            rsi_signal = f"Neutral ({rsi})"

    return {
        "rsi": rsi,
        "rsi_signal": rsi_signal,
        "ema20": ema20,
        "ema50": ema50,
        "ema_signal": ema_signal,
        "price_position_pct": price_position,
    }