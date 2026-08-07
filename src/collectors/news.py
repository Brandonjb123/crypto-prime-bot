"""Google News RSS collector."""

import feedparser
from loguru import logger

from src.core.interfaces.base_collector import BaseCollector
from src.core.models.normalized_asset import RawNewsData


class NewsCollector(BaseCollector):
    """Collect news headlines dari Google News RSS."""

    MAX_ARTICLES = 5

    async def fetch(self, symbol: str) -> RawNewsData:
        """Fetch top 5 headlines untuk symbol."""
        query = f"{symbol} crypto"
        url = f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en"
        logger.debug(f"Fetching news for {symbol}")

        feed = feedparser.parse(url)
        headlines = [entry.get("title", "") for entry in feed.entries[: self.MAX_ARTICLES]]

        return RawNewsData(
            symbol=symbol,
            headlines=headlines,
            article_count=len(headlines),
        )

    async def health_check(self) -> bool:
        try:
            feed = feedparser.parse("https://news.google.com/rss/search?q=bitcoin&hl=en")
            return len(feed.entries) > 0
        except Exception:
            return False
