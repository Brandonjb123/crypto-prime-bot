from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class SubscriptionStatus(StrEnum):
    FREE = "free"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    chat_id: int
    plan: str = "early_access"
    status: SubscriptionStatus = SubscriptionStatus.FREE
    start_date: datetime | None = None
    expiry_date: datetime | None = None
    payment_reference: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))