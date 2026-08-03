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
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def get(self, endpoint: str, params: dict | None = None) -> dict:
        """GET request dengan retry logic (hanya untuk 429 dan 5xx)."""
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self.client.get(url, params=params)

                # 429 — Rate limit
                if response.status_code == 429:
                    wait = self.RETRY_DELAY * (2**attempt)
                    logger.warning(f"429 Rate limit {url}, retry in {wait}s")
                    await asyncio.sleep(wait)
                    if attempt == self.MAX_RETRIES - 1:
                        raise RateLimitError(f"Rate limit exceeded: {url}")
                    continue

                # 5xx — Server error
                if response.status_code >= 500:
                    logger.warning(
                        f"5xx server error {response.status_code} {url}, "
                        f"attempt {attempt + 1}"
                    )
                    if attempt == self.MAX_RETRIES - 1:
                        raise DataSourceUnavailableError(
                            f"Server error {response.status_code}: {url}"
                        )
                    continue

                # Sukses atau client error (4xx selain 429) — jangan retry
                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException:
                logger.warning(f"Timeout {url} attempt {attempt + 1}")
                if attempt == self.MAX_RETRIES - 1:
                    raise DataSourceUnavailableError(f"Timeout: {url}") from None
                continue

        raise DataSourceUnavailableError(
            f"Failed after {self.MAX_RETRIES} retries"
        )

    async def close(self) -> None:
        """Tutup AsyncClient."""
        await self.client.aclose()