"""In-memory price provider — no network, deterministic."""


class InMemoryPriceProvider:
    """Simple price provider dengan penyimpanan in-memory."""

    def __init__(self) -> None:
        self._prices: dict[str, float] = {}

    def update_price(self, symbol: str, price: float) -> None:
        """Update harga untuk symbol."""
        self._prices[symbol] = price

    def get_price(self, symbol: str) -> float | None:
        """Dapatkan harga terbaru, atau None jika tidak tersedia."""
        return self._prices.get(symbol)
