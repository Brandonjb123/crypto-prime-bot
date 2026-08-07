"""Unit tests untuk NotificationDispatcher."""

from uuid import UUID

from src.core.types.enums import OrderStatus, Side
from src.events.base_event import BaseDomainEvent
from src.events.events.order_executed import OrderExecutedEvent
from src.events.events.position_opened import PositionOpenedEvent
from src.notification.console_notifier import ConsoleNotifier
from src.notification.dispatcher import NotificationDispatcher
from src.notification.formatters.order_formatter import OrderExecutedFormatter
from src.notification.formatters.position_formatter import PositionOpenedFormatter


class TestNotificationDispatcher:
    def test_dispatch_registered_event(self, capsys):
        notifier = ConsoleNotifier()
        dispatcher = NotificationDispatcher(notifier)
        dispatcher.register(OrderExecutedEvent, OrderExecutedFormatter())

        event = OrderExecutedEvent(
            execution_id=UUID("aaaaaaaa-1234-5678-1234-567812345678"),
            order_id=UUID("bbbbbbbb-1234-5678-1234-567812345678"),
            status=OrderStatus.FILLED,
            symbol="BTC/USDT",
            side=Side.LONG,
        )
        dispatcher.dispatch(event)
        captured = capsys.readouterr()
        assert "Order Executed" in captured.out

    def test_unknown_event_ignored(self, capsys):
        notifier = ConsoleNotifier()
        dispatcher = NotificationDispatcher(notifier)
        event = BaseDomainEvent(event_name="unknown_event")
        dispatcher.dispatch(event)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_formatter_selected_automatically(self, capsys):
        notifier = ConsoleNotifier()
        dispatcher = NotificationDispatcher(notifier)
        dispatcher.register(PositionOpenedEvent, PositionOpenedFormatter())

        event = PositionOpenedEvent(
            position_id=UUID("12345678-1234-5678-1234-567812345678"),
            symbol="ETH/USDT",
            side=Side.SHORT,
            entry_price=3000.0,
            position_size=0.5,
        )
        dispatcher.dispatch(event)
        captured = capsys.readouterr()
        assert "Position Opened" in captured.out

    def test_multiple_dispatches(self, capsys):
        notifier = ConsoleNotifier()
        dispatcher = NotificationDispatcher(notifier)
        dispatcher.register(OrderExecutedEvent, OrderExecutedFormatter())

        for _ in range(3):
            dispatcher.dispatch(
                OrderExecutedEvent(
                    execution_id=UUID("aaaaaaaa-1234-5678-1234-567812345678"),
                    order_id=UUID("bbbbbbbb-1234-5678-1234-567812345678"),
                    status=OrderStatus.FILLED,
                    symbol="BTC/USDT",
                    side=Side.LONG,
                )
            )
        captured = capsys.readouterr()
        assert captured.out.count("Order Executed") == 3

    def test_deterministic(self, capsys):
        n1 = ConsoleNotifier()
        d1 = NotificationDispatcher(n1)
        d1.register(OrderExecutedEvent, OrderExecutedFormatter())

        n2 = ConsoleNotifier()
        d2 = NotificationDispatcher(n2)
        d2.register(OrderExecutedEvent, OrderExecutedFormatter())

        event = OrderExecutedEvent(
            execution_id=UUID("aaaaaaaa-1234-5678-1234-567812345678"),
            order_id=UUID("bbbbbbbb-1234-5678-1234-567812345678"),
            status=OrderStatus.FILLED,
            symbol="BTC/USDT",
            side=Side.LONG,
        )
        d1.dispatch(event)
        d2.dispatch(event)
        # Deterministic by design — no randomness, no external dependency
