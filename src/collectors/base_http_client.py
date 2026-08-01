"""Shared async HTTP client dengan retry dan timeout."""

import asyncio

import httpx
from loguru import logger

from src.core.exceptions.collector_exceptions import (
    DataSourceUnavailableError,
    RateLimitError,
)


class BaseHTTPClient:
    """Reusable async HTTP client untuk semua collectors."""

    DEFAULT_TIMEOUT = 10.0
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0

    def __init__(self, base_url: str, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.base_url = base_url
        self.timeout = timeout

    async def get(self, endpoint: str, params: dict | None = None) -> dict:
        """GET request dengan retry logic."""
        url = f"{self.base_url}{endpoint}"
        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params)
                    if response.status_code == 429:
                        wait = self.RETRY_DELAY * (2**attempt)
                        logger.warning(f"Rate limit hit {url}, retry in {wait}s")
                        await asyncio.sleep(wait)
                        raise RateLimitError(f"Rate limit: {url}")
                    response.raise_for_status()
                    return response.json()
            except RateLimitError:
                if attempt == self.MAX_RETRIES - 1:
                    raise DataSourceUnavailableError(f"Rate limit exceeded: {url}") from None
                continue
            except httpx.TimeoutException:
                logger.warning(f"Timeout {url} attempt {attempt + 1}")
                if attempt == self.MAX_RETRIES - 1:
                    raise DataSourceUnavailableError(f"Timeout: {url}") from None
            except httpx.HTTPError as e:
                raise DataSourceUnavailableError(f"HTTP error: {e}") from e
        raise DataSourceUnavailableError(f"Failed after {self.MAX_RETRIES} retries")