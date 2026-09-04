"""Base Domain Event model — immutable."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict


class BaseDomainEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: UUID = uuid4()
    event_name: str
    timestamp: datetime = datetime.now(UTC)
