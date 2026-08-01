from abc import ABC, abstractmethod

from src.core.models.normalized_asset import NormalizedAsset


class BaseCollector(ABC):
    """Abstract base class untuk semua data collectors."""

    @abstractmethod
    async def fetch(self, symbol: str) -> NormalizedAsset:
        """Fetch raw data untuk symbol yang diberikan."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check apakah source ini available."""
        ...
