"""Unit tests untuk Domain Events."""

import json
from uuid import UUID

from src.core.types.enums import OrderStatus, PositionCloseReason, Side
from src.events.base_event import BaseDomainEvent
from src.events.events.order_executed import OrderExecutedEvent
from src.events.events.portfolio_updated import PortfolioUpdatedEvent
from src.events.events.position_closed import PositionClosedEvent
from src.events.events.position_opened import PositionOpenedEvent


class TestDomainEvents:
    def test_position_opened_event(self):
        event = PositionOpenedEvent(
            position_id=UUID("12345678-1234-5678-1234-567812345678"),
            symbol="BTC/USDT",
            side=Side.LONG,
            entry_price=50000.0,
            position_size=0.1,
        )
        assert event.event_name == "position_opened"
        assert isinstance(event.event_id, UUID)
        assert event.position_id == UUID("12345678-1234-5678-1234-567812345678")

    def test_position_closed_event(self):
        event = PositionClosedEvent(
            position_id=UUID("12345678-1234-5678-1234-567812345678"),
            reason=PositionCloseReason.STOP_LOSS,
            exit_price=48000.0,
        )
        assert event.event_name == "position_closed"
        assert event.reason == PositionCloseReason.STOP_LOSS

    def test_order_executed_event(self):
        event = OrderExecutedEvent(
            execution_id=UUID("aaaaaaaa-1234-5678-1234-567812345678"),
            order_id=UUID("bbbbbbbb-1234-5678-1234-567812345678"),
            status=OrderStatus.FILLED,
            symbol="BTC/USDT",
            side=Side.LONG,
        )
        assert event.event_name == "order_executed"
        assert event.status == OrderStatus.FILLED

    def test_portfolio_updated_event(self):
        event = PortfolioUpdatedEvent(
            snapshot_id=UUID("cccccccc-1234-5678-1234-567812345678"),
            equity=15000.0,
            gross_exposure=0.5,
            net_exposure=0.2,
        )
        assert event.event_name == "portfolio_updated"

    def test_event_immutable(self):
        import pytest
        from pydantic import ValidationError

        event = BaseDomainEvent(event_name="test")
        with pytest.raises(ValidationError):
            event.event_name = "changed"

    def test_event_serializable(self):
        event = PositionOpenedEvent(
            position_id=UUID("12345678-1234-5678-1234-567812345678"),
            symbol="BTC/USDT",
            side=Side.LONG,
            entry_price=50000.0,
            position_size=0.1,
        )
        data = json.loads(event.model_dump_json())
        assert data["symbol"] == "BTC/USDT"
