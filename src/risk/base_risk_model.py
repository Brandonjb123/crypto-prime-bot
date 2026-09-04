"""Abstract base risk model — Strategy Pattern."""

from abc import ABC, abstractmethod

from src.core.models.risk import RiskResult
from src.core.models.setup import SetupResult
from src.core.models.snapshot import AnalysisSnapshot
from src.core.models.validation import ValidationResult


class BaseRiskModel(ABC):
    """Abstract risk model untuk setiap tipe setup."""

    @abstractmethod
    def calculate(
        self,
        snapshot: AnalysisSnapshot,
        setup: SetupResult,
        validation: ValidationResult,
    ) -> RiskResult:
        """Hitung position size, SL, TP, dan risk metrics."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Nama model risiko (contoh: 'trend', 'breakout', 'reversal')."""
        ...
