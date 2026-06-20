# services/scanner.py
import asyncio
import json
from services.coingecko import get_market_data, get_top_pairs
from services.news import get_news
from services.llm import ask_llm
from prompts.system import SYSTEM_PROMPT
from prompts.templates import build_analyze_prompt
from loguru import logger
from utils.validator import inject_calculated_prices, validate_signal_prices

# Daftar simbol yang termasuk top 10 market cap
TOP_MCAP_SYMBOLS = {"BTC", "ETH", "BNB", "XRP", "SOL", "ADA", "DOGE", "AVAX", "DOT", "LINK"}


def _sort_signals_by_rr(signals: list) -> list:
    """Urutkan sinyal berdasarkan R:R ratio (tertinggi ke terendah)."""
    return sorted(
        signals,
        key=lambda x: (
            (x.get("target_price", 0) - x.get("entry_price", 0)) /
            max(x.get("entry_price", 0) - x.get("stop_loss", 1), 0.000001)
        ),
        reverse=True
    )


async def scan_market(limit: int = 100) -> list:
    """Scan top {limit} pair, return list sinyal LAYAK (max 10, ter-diversifikasi)."""
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
            try:
                raw = await ask_llm(SYSTEM_PROMPT, prompt)
                data = json.loads(raw)
                data = inject_calculated_prices(data)
            except json.JSONDecodeError:
                logger.warning(f"JSON parse error untuk {symbol}")
                continue
            except Exception as e:
                logger.warning(f"Groq/API error untuk {symbol}: {e}")
                continue

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

    # --- DIVERSIFIKASI HASIL ---
    # Pisahkan top market cap dari sisanya
    top_mcap_results = [r for r in results if r["pair"].split("/")[0] in TOP_MCAP_SYMBOLS]
    other_results = [r for r in results if r["pair"].split("/")[0] not in TOP_MCAP_SYMBOLS]

    # Urutkan masing-masing berdasarkan R:R (terbaik duluan)
    top_mcap_results = _sort_signals_by_rr(top_mcap_results)
    other_results = _sort_signals_by_rr(other_results)

    # Gabungkan: maksimal 3 dari top market cap, sisanya dari yang lain
    final_results = top_mcap_results[:3] + other_results[:7]

    return final_results[:10]