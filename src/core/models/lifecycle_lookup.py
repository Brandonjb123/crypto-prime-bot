"""Lifecycle lookup DTOs — structured result for read-only lookups.

Used by display layer via SignalLifecycleRepository port.
- Found : row exists (signal_id -> LifecycleRecord)
- Absent: query succeeded, no row for these signal_ids
- Failed: query raised / chunk failed / unsupported for these signal_ids

Absent vs Failed distinction is load-bearing: only Absent may be used
for LEGACY/RECENT classification; Failed must produce UNKNOWN.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class LifecycleRecord:
    signal_id: UUID
    status: str
    expires_at: datetime | None = None


@dataclass(frozen=True)
class LifecycleLookupResult:
    found: dict[UUID, LifecycleRecord] = field(default_factory=dict)
    absent: set[UUID] = field(default_factory=set)
    failed: set[UUID] = field(default_factory=set)