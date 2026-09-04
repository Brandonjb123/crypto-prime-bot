"""Fear & Greed Index collector."""

from loguru import logger

from src.collectors.base_http_client import BaseHTTPClient
from src.core.interfaces.base_collector import BaseCollector
from src.core.models.normalized_asset import RawFearGreedData

FEAR_GREED_BASE_URL = "https://api.alternative.me"


class FearGreedCollector(BaseCollector):
    """Collect Fear & Greed Index dari alternative.me."""

    def __init__(self) -> None:
        self.client = BaseHTTPClient(FEAR_GREED_BASE_URL)

    async def fetch(self, symbol: str = "market") -> RawFearGreedData:
        """Fetch Fear & Greed Index. Symbol diabaikan (market-wide)."""
        logger.debug("Fetching Fear & Greed Index")

        data = await self.client.get("/fng/", params={"limit": 1})
        entry = data["data"][0]

        return RawFearGreedData(
            symbol="market",
            value=int(entry["value"]),
            classification=entry["value_classification"],
            timestamp=int(entry["timestamp"]),
        )

    async def health_check(self) -> bool:
        try:
            await self.client.get("/fng/", params={"limit": 1})
            return True
        except Exception:
            return False
