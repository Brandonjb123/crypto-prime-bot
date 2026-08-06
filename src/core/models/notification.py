"""Notification message model — immutable."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.core.types.enums import NotificationLevel


class NotificationMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    message_id: UUID
    title: str
    body: str
    level: NotificationLevel
    timestamp: datetime