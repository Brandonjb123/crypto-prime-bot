"""SignalLifecycle repository interface — dedicated persistence boundary."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.core.models.signal_lifecycle import SignalLifecycle
from src.core.types.enums import SignalLifecycleExpireReason


class SignalLifecycleRepository(ABC):
    @abstractmethod
    def get_active_by_symbol(self, symbol: str) -> SignalLifecycle | None:
        """Return ACTIVE lifecycle untuk symbol, atau None."""
        ...

    @abstractmethod
    def create_with_supersede(
        self, new_lifecycle: SignalLifecycle
    ) -> SignalLifecycle:
        """Atomic: expire existing ACTIVE for symbol, insert new as ACTIVE."""
        ...

    @abstractmethod
    def mark_expired(
        self, signal_id: UUID, reason: SignalLifecycleExpireReason
    ) -> None:
        """Mark lifecycle as EXPIRED. Idempotent untuk non-ACTIVE."""
        ...