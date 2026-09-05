"""Background price refresh service — updates price provider periodically."""

import asyncio

import httpx
from loguru import logger

DEFAULT_SYMBOLS = [
    "BTC", "ETH", "BNB", "SOL", "XRP",
    "DOGE", "ADA", "AVAX", "LINK",
]
BINANCE_TICKER_URL = "https://data-api.binance.vision/api/v3/ticker/price"


class PriceRefreshService:
    def __init__(
        self,
        price_provider,
        symbols: list[str] | None = None,
        interval_seconds: int = 60,
        http_client: httpx.AsyncClient | None = None,
    ):
        self.price_provider = price_provider
        self.symbols = symbols or DEFAULT_SYMBOLS
        self.interval_seconds = interval_seconds
        self._client = http_client or httpx.AsyncClient(timeout=10.0)
        self._task: asyncio.Task | None = None
        self._running = False

    async def refresh_once(self) -> None:
        """Ambil harga terbaru semua symbol dan update provider."""
        for sym in self.symbols:
            try:
                url = f"{BINANCE_TICKER_URL}?symbol={sym}USDT"
                resp = await self._client.get(url)
                resp.raise_for_status()
                data = resp.json()
                price = float(data["price"])
                self.price_provider.update_price(sym, price)
                logger.info(f"[price_refresh] {sym} -> {price}")
            except Exception as e:
                logger.warning(f"[price_refresh] gagal untuk {sym}: {e}")

    async def _run_loop(self) -> None:
        self._running = True
        while self._running:
            await self.refresh_once()
            await asyncio.sleep(self.interval_seconds)

    def start(self) -> None:
        """Jalankan background task."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run_loop())
            logger.info("[price_refresh] background task started")

    async def stop(self) -> None:
        """Hentikan background task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("[price_refresh] background task stopped")