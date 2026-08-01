"""Registry semua collectors — single point of access."""

from loguru import logger

from src.collectors.binance import BinanceCollector
from src.collectors.coingecko import CoinGeckoCollector
from src.collectors.fear_greed import FearGreedCollector
from src.collectors.news import NewsCollector


class CollectorRegistry:
    """Orchestrate semua collectors untuk satu symbol."""

    def __init__(self) -> None:
        self.binance = BinanceCollector()
        self.coingecko = CoinGeckoCollector()
        self.fear_greed = FearGreedCollector()
        self.news = NewsCollector()

    async def collect_all(self, symbol: str) -> dict:
        """
        Collect dari semua sources untuk satu symbol.
        Graceful degrade: gagal satu source tidak stop yang lain.
        """
        results = {
            "symbol": symbol,
            "binance": None,
            "coingecko": None,
            "fear_greed": None,
            "news": None,
            "data_quality_score": 0.0,
        }

        # Binance — kritis
        try:
            results["binance"] = await self.binance.fetch(symbol)
        except Exception as e:
            logger.warning(f"Binance fetch failed for {symbol}: {e}")

        # CoinGecko — kritis
        try:
            results["coingecko"] = await self.coingecko.fetch(symbol)
        except Exception as e:
            logger.warning(f"CoinGecko fetch failed for {symbol}: {e}")

        # Fear & Greed — non-kritis
        try:
            results["fear_greed"] = await self.fear_greed.fetch()
        except Exception as e:
            logger.warning(f"Fear & Greed fetch failed: {e}")

        # News — non-kritis
        try:
            results["news"] = await self.news.fetch(symbol)
        except Exception as e:
            logger.warning(f"News fetch failed for {symbol}: {e}")

        # Hitung data quality score
        critical_sources = ["binance", "coingecko"]
        non_critical_sources = ["fear_greed", "news"]
        critical_ok = sum(1 for s in critical_sources if results[s] is not None)
        non_critical_ok = sum(1 for s in non_critical_sources if results[s] is not None)
        results["data_quality_score"] = (
            (critical_ok / len(critical_sources)) * 0.7
            + (non_critical_ok / len(non_critical_sources)) * 0.3
        )

        logger.info(
            f"Collected {symbol} — quality: {results['data_quality_score']:.0%} "
            f"(Binance: {'✓' if results['binance'] else '✗'}, "
            f"CoinGecko: {'✓' if results['coingecko'] else '✗'})"
        )

        return results

    async def health_check_all(self) -> dict[str, bool]:
        """Check semua collectors."""
        return {
            "binance": await self.binance.health_check(),
            "coingecko": await self.coingecko.health_check(),
            "fear_greed": await self.fear_greed.health_check(),
            "news": await self.news.health_check(),
        }