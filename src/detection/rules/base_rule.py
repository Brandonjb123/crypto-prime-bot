"""Abstract base rule untuk Setup Detection."""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from src.core.models.snapshot import AnalysisSnapshot
from src.core.types.enums import Side


class RuleResult(BaseModel):
    """Hasil evaluasi satu rule."""

    passed: bool
    direction: Side | None = None
    reasons: list[str] = []


class BaseRule(ABC):
    """Abstract base class untuk semua detection rules."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nama rule (contoh: 'trend_following')."""
        ...

    @abstractmethod
    def evaluate(self, snapshot: AnalysisSnapshot) -> RuleResult:
        """Evaluasi apakah rule ini triggered pada snapshot."""
        ...
