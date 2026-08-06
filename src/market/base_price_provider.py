"""Base Price Provider interface."""

from abc import ABC, abstractmethod


class BasePriceProvider(ABC):
    """Abstract interface untuk price provider."""

    @abstractmethod
    def get_price(self, symbol: str) -> float | None:
        """Return harga terbaru untuk symbol, atau None jika tidak tersedia."""
        ...