"""SignalLifecycle repository interface — dedicated persistence boundary."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.core.models.lifecycle_lookup import LifecycleLookupResult
from src.core.models.signal_lifecycle import SignalLifecycle
from src.core.types.enums import SignalLifecycleExpireReason


class SignalLifecycleRepository(ABC):
    @abstractmethod
    def get_active_by_symbol(self, symbol: str) -> SignalLifecycle | None:
        """Return ACTIVE lifecycle untuk symbol, atau None."""
        ...

    @abstractmethod
    def get_all_active(self) -> list[SignalLifecycle]:
        """Return semua lifecycle dengan status ACTIVE (untuk evaluation cycle)."""
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

    @abstractmethod
    def get_lifecycle_lookup(
        self, signal_ids: list[UUID]
    ) -> LifecycleLookupResult:
        """Read-only bulk lifecycle lookup for display purposes.

        Returns LifecycleLookupResult with found / absent / failed buckets:
          - found : row exists (signal_id -> LifecycleRecord)
          - absent: query succeeded, no row for this signal_id
          - failed: query failed, timed out, or unsupported for this signal_id

        Failed must NOT be disguised as absent — display layer relies on the
        distinction to avoid misclassifying as LEGACY/RECENT.
        """
        ...