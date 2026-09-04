"""In-memory price provider — no network, deterministic."""


class InMemoryPriceProvider:
    """Simple price provider dengan penyimpanan in-memory dan normalisasi simbol."""

    def __init__(self) -> None:
        self._prices: dict[str, float] = {}

    @staticmethod
    def _normalize(symbol: str) -> str:
        """Normalisasi symbol menjadi base currency tanpa suffix /USDT atau USDT."""
        s = symbol.upper().strip()
        if s.endswith("/USDT"):
            s = s[:-5]
        elif s.endswith("USDT"):
            s = s[:-4]
        return s

    def update_price(self, symbol: str, price: float) -> None:
        """Update harga untuk symbol (dinormalisasi)."""
        key = self._normalize(symbol)
        self._prices[key] = price

    def get_price(self, symbol: str) -> float | None:
        """Dapatkan harga terbaru, atau None jika tidak tersedia."""
        key = self._normalize(symbol)
        return self._prices.get(key)

    def update_price(self, symbol: str, price: float) -> None:
        print(f"DEBUG price update: {symbol} -> {price}")
        key = self._normalize(symbol)
        self._prices[key] = price