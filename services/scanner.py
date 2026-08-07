# services/scanner.py
import asyncio
import json
import random

from loguru import logger

from prompts.system import SYSTEM_PROMPT
from prompts.templates import build_analyze_prompt
from services.coingecko import get_market_data, get_technical_indicators, get_top_pairs
from services.llm import ask_llm
from services.news import get_news
from utils.validator import inject_calculated_prices, validate_signal_prices


def _sort_signals_by_rr(signals: list) -> list:
    return sorted(
        signals,
        key=lambda x: (
            (x.get("target_price", 0) - x.get("entry_price", 0))
            / max(x.get("entry_price", 0) - x.get("stop_loss", 1), 0.000001)
        ),
        reverse=True,
    )


async def scan_market(limit: int = 100) -> list:
    top_pairs = await get_top_pairs(limit)

    random.shuffle(top_pairs)

    results = []
    scanned = 0

    for pair_info in top_pairs:
        try:
            symbol = pair_info["symbol"]
            coin_id = pair_info["coin_id"]

            # Fetch market data (dengan retry handling)
            try:
                price_data = await get_market_data(coin_id)
            except Exception as e:
                if "429" in str(e):
                    await asyncio.sleep(10)  # Tunggu 10 detik jika rate limit
                    continue
                continue

            if not price_data or not price_data.get("current_price"):
                continue

            news = await get_news(symbol)
            headlines = [item["title"] for item in news[:5]]

            indicators = await get_technical_indicators(coin_id)

            prompt = build_analyze_prompt(symbol, price_data, headlines, indicators)
            try:
                raw = await ask_llm(SYSTEM_PROMPT, prompt)
                data = json.loads(raw)
                data = inject_calculated_prices(data)
            except json.JSONDecodeError:
                logger.warning(f"JSON parse error untuk {symbol}")
                continue
            except Exception as e:
                logger.warning(f"API error untuk {symbol}: {e}")
                continue

            if data.get("verdict") == "SETUP_VALID":
                current_price = price_data.get("current_price", 0)
                if validate_signal_prices(data, current_price):
                    data["pair"] = f"{symbol}/USDT"
                    data["price_data"] = price_data
                    results.append(data)

                    if len(results) >= 10:
                        break

        except Exception as e:
            logger.warning(f"Scan {symbol} error: {e}")
            continue

        scanned += 1
        await asyncio.sleep(1.5)

    return _sort_signals_by_rr(results)[:10]
