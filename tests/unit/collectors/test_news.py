"""Unit tests untuk NewsCollector."""

import feedparser
import pytest

from src.collectors.news import NewsCollector
from src.core.models.normalized_asset import RawNewsData


@pytest.mark.asyncio
async def test_news_fetch_success(monkeypatch):
    """Test fetch sukses return RawNewsData."""

    mock_feed = feedparser.FeedParserDict(
        entries=[
            feedparser.FeedParserDict(title="Bitcoin hits new all-time high"),
            feedparser.FeedParserDict(title="SEC approves spot Bitcoin ETF"),
            feedparser.FeedParserDict(title="Bitcoin Layer 2 solutions gain traction"),
            feedparser.FeedParserDict(title="Crypto market cap reaches $3 trillion"),
            feedparser.FeedParserDict(title="Bitcoin mining difficulty hits record high"),
        ]
    )

    def mock_parse(url):
        return mock_feed

    monkeypatch.setattr(feedparser, "parse", mock_parse)

    collector = NewsCollector()
    result = await collector.fetch("BTC")

    assert isinstance(result, RawNewsData)
    assert result.symbol == "BTC"
    assert len(result.headlines) == 5
    assert result.article_count == 5
    assert "Bitcoin hits new all-time high" in result.headlines


@pytest.mark.asyncio
async def test_news_fetch_empty(monkeypatch):
    """Test fetch dengan hasil kosong."""

    mock_feed = feedparser.FeedParserDict(entries=[])

    def mock_parse(url):
        return mock_feed

    monkeypatch.setattr(feedparser, "parse", mock_parse)

    collector = NewsCollector()
    result = await collector.fetch("BTC")

    assert result.article_count == 0
    assert result.headlines == []


@pytest.mark.asyncio
async def test_news_health_check(monkeypatch):
    """Test health check News."""

    mock_feed = feedparser.FeedParserDict(entries=[feedparser.FeedParserDict(title="Test")])

    def mock_parse(url):
        return mock_feed

    monkeypatch.setattr(feedparser, "parse", mock_parse)

    collector = NewsCollector()
    assert await collector.health_check() is True
