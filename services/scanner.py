# services/scanner.py
import asyncio
import json
from services.coingecko import get_market_data, get_top_pairs
from services.news import get_news
from services.llm import ask_llm
from prompts.system import SYSTEM_PROMPT
from prompts.templates import build_analyze_prompt
from loguru import logger
from utils.validator import validate_signal_prices


async def scan_market(limit: int = 100) -> list:
    """Scan top {limit} pair, return list signal yang LAYAK (max 10)."""
    top_pairs = await get_top_pairs(limit)
    results = []

    for i, pair_info in enumerate(top_pairs):
        try:
            symbol = pair_info["symbol"]
            coin_id = pair_info["coin_id"]

            # Fetch market data
            price_data = await get_market_data(coin_id)
            if not price_data or not price_data.get("current_price"):
                continue

            # Fetch news
            news = await get_news(symbol)
            headlines = [item["title"] for item in news[:5]]

            # Build prompt & call LLM
            prompt = build_analyze_prompt(symbol, price_data, headlines)
            raw = await ask_llm(SYSTEM_PROMPT, prompt)

            data = json.loads(raw)
            if data.get("verdict") == "SETUP_VALID":
                current_price = price_data.get("current_price", 0)
                if validate_signal_prices(data, current_price):
                    data["pair"] = f"{symbol}/USDT"
                    data["price_data"] = price_data
                    results.append(data)

        except Exception as e:
            logger.warning(f"Scan {symbol} error: {e}")
            continue

        # Rate limit protection
        await asyncio.sleep(0.5)

    # Sort by R:R ratio (terbaik duluan)
    results.sort(
        key=lambda x: (
            (x.get("target_price", 0) - x.get("entry_price", 0)) /
            max(x.get("entry_price", 0) - x.get("stop_loss", 1), 0.000001)
        ),
        reverse=True
    )

    return results[:10]