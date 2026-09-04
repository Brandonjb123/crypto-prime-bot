"""Unit tests untuk formatters."""

from uuid import UUID

from src.core.models.notification import NotificationMessage
from src.core.types.enums import NotificationLevel, OrderStatus, PositionCloseReason, Side
from src.events.events.order_executed import OrderExecutedEvent
from src.events.events.portfolio_updated import PortfolioUpdatedEvent
from src.events.events.position_closed import PositionClosedEvent
from src.events.events.position_opened import PositionOpenedEvent
from src.notification.formatters.order_formatter import OrderExecutedFormatter
from src.notification.formatters.portfolio_formatter import PortfolioUpdatedFormatter
from src.notification.formatters.position_formatter import (
    PositionClosedFormatter,
    PositionOpenedFormatter,
)


class TestFormatters:
    def test_order_executed_format(self):
        event = OrderExecutedEvent(
            execution_id=UUID("aaaaaaaa-1234-5678-1234-567812345678"),
            order_id=UUID("bbbbbbbb-1234-5678-1234-567812345678"),
            status=OrderStatus.FILLED,
            symbol="BTC/USDT",
            side=Side.LONG,
        )
        msg = OrderExecutedFormatter().format(event)
        assert isinstance(msg, NotificationMessage)
        assert msg.title == "Order Executed"
        assert msg.level == NotificationLevel.INFO
        assert "BTC/USDT" in msg.body

    def test_position_opened_format(self):
        event = PositionOpenedEvent(
            position_id=UUID("12345678-1234-5678-1234-567812345678"),
            symbol="BTC/USDT",
            side=Side.LONG,
            entry_price=50000.0,
            position_size=0.1,
        )
        msg = PositionOpenedFormatter().format(event)
        assert msg.title == "Position Opened"
        assert "50000" in msg.body

    def test_position_closed_format(self):
        event = PositionClosedEvent(
            position_id=UUID("12345678-1234-5678-1234-567812345678"),
            reason=PositionCloseReason.STOP_LOSS,
            exit_price=48000.0,
        )
        msg = PositionClosedFormatter().format(event)
        assert msg.title == "Position Closed"
        assert "STOP_LOSS" in msg.body

    def test_portfolio_updated_format(self):
        event = PortfolioUpdatedEvent(
            snapshot_id=UUID("cccccccc-1234-5678-1234-567812345678"),
            equity=15000.0,
            gross_exposure=0.5,
            net_exposure=0.2,
        )
        msg = PortfolioUpdatedFormatter().format(event)
        assert msg.title == "Portfolio Updated"
        assert "15000" in msg.body
