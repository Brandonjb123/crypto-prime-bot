from abc import ABC, abstractmethod

from src.core.models.normalized_asset import NormalizedAsset
from src.core.types.signal import AnalysisResult


class BaseAnalyzer(ABC):
    """Abstract base class untuk semua analysis modules."""

    @abstractmethod
    async def analyze(self, asset: NormalizedAsset) -> AnalysisResult:
        """Analisa asset dan return result."""
        ...

    @property
    @abstractmethod
    def weight(self) -> float:
        """Bobot module ini di Confidence Engine (0.0 - 1.0)."""
        ...
