"""Read-only lifecycle lookup port.

Display surfaces must depend only on this protocol — never on the full
SignalLifecycleRepository (which includes write methods like mark_expired).
"""

from typing import Protocol
from uuid import UUID

from src.core.models.lifecycle_lookup import LifecycleLookupResult


class LifecycleReadPort(Protocol):
    def get_lifecycle_lookup(
        self, signal_ids: list[UUID]
    ) -> LifecycleLookupResult:
        """Read-only bulk lifecycle lookup."""
        ...