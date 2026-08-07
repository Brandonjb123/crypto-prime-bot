"""PortfolioUpdatedEvent — dipublikasi saat portfolio snapshot dibuat."""

from uuid import UUID

from src.events.base_event import BaseDomainEvent


class PortfolioUpdatedEvent(BaseDomainEvent):
    event_name: str = "portfolio_updated"
    snapshot_id: UUID
    equity: float
    gross_exposure: float
    net_exposure: float
