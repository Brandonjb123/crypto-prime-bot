"""Audit record model."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel

from src.core.types.enums import AuditEventType


class AuditRecord(BaseModel):
    audit_id: UUID = uuid4()
    event_type: AuditEventType
    message: str
    timestamp: datetime
