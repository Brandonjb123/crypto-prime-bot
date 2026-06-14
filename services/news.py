# services/news.py
import asyncio
import feedparser
from urllib.parse import quote
from utils.cache import news_cache
from loguru import logger

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={}&hl=en&gl=US&ceid=US:en"

async def get_news(pair: str) -> list:
    cached = news_cache.get(pair)
    if cached:
        logger.info(f"Cache hit for news {pair}")
        return cached

    keyword = pair.upper()
    MAPPING = {
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "BNB": "Binance Coin",
        "XRP": "Ripple",
        "ADA": "Cardano",
        "SOL": "Solana",
        "DOGE": "Dogecoin",
        "DOT": "Polkadot",
    }
    query = MAPPING.get(keyword, keyword) + " crypto"
    url = GOOGLE_NEWS_RSS.format(quote(query))

    loop = asyncio.get_running_loop()
    feed = await loop.run_in_executor(None, feedparser.parse, url)

    articles = []
    for entry in feed.entries[:5]:
        source = "Unknown"
        if hasattr(entry, "source") and entry.source:
            source = entry.source.get("title", "Unknown")
        articles.append({
            "title": entry.title,
            "source": source,
            "url": entry.link,
            "published": entry.published,
        })

    news_cache.set(pair, articles)
    logger.info(f"Fetched {len(articles)} news for {pair}")
    return articles