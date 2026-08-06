"""Synchronization result model."""

from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel
from src.core.types.enums import SyncEntityType, SyncReason, SyncStatus


class SyncResult(BaseModel):
    sync_id: UUID = uuid4()
    status: SyncStatus
    entity_type: SyncEntityType
    synced_count: int
    mismatch_count: int
    reasons: list[SyncReason]
    details: list[str]
    timestamp: datetime