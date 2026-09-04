"""Unit tests untuk NotificationEngine."""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

from src.core.models.position import Position
from src.core.models.trading_signal import TradingSignal
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.notification.notification_engine import NotificationEngine


def _make_signal(**overrides):
    defaults = dict(
        signal_id=uuid4(),
        symbol="BTC",
        side="BUY",
        status="ACTIVE",
        entry_price=50000.0,
        stop_loss=48000.0,
        take_profit=55000.0,
        position_size=0.01,
        risk_percent=2.0,
        confidence=85,
        risk_level="MEDIUM",
        reasoning=["Bullish trend", "Strong momentum"],
        created_at=datetime.now(UTC),
    )
    defaults.update(overrides)
    return TradingSignal(**defaults)


def _make_position():
    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        symbol="BTC",
        side=Side.LONG,
        status=PositionStatus.OPEN,
        entry_price=50000.0,
        stop_loss=48000.0,
        take_profit=55000.0,
        position_size=0.01,
        opened_at=datetime.now(UTC),
        closed_at=None,
        close_reason=PositionCloseReason.NONE,
    )


class TestNotificationEngine:
    def test_active_buy_notification(self):
        notifier = MagicMock()
        engine = NotificationEngine(notifier)
        signal = _make_signal(side="BUY")
        engine.notify_signal(signal)

        assert notifier.notify.called
        msg = notifier.notify.call_args[0][0]
        assert "BUY" in msg.body
        assert "50000" in msg.body
        assert "Bullish trend" in msg.body

    def test_active_sell_notification(self):
        notifier = MagicMock()
        engine = NotificationEngine(notifier)
        signal = _make_signal(side="SELL")
        engine.notify_signal(signal)

        msg = notifier.notify.call_args[0][0]
        assert "SELL" in msg.body

    def test_skipped_signal_notification(self):
        notifier = MagicMock()
        engine = NotificationEngine(notifier)
        signal = _make_signal(status="SKIPPED")
        engine.notify_signal(signal)

        msg = notifier.notify.call_args[0][0]
        assert "Skipped" in msg.title

    def test_invalid_signal_notification(self):
        notifier = MagicMock()
        engine = NotificationEngine(notifier)
        signal = _make_signal(status="INVALID")
        engine.notify_signal(signal)

        msg = notifier.notify.call_args[0][0]
        assert "Invalid" in msg.title

    def test_reasoning_formatting(self):
        notifier = MagicMock()
        engine = NotificationEngine(notifier)
        signal = _make_signal(reasoning=["Reason 1", "Reason 2"])
        engine.notify_signal(signal)

        msg = notifier.notify.call_args[0][0]
        assert "Reason 1" in msg.body
        assert "Reason 2" in msg.body

    def test_position_opened_notification(self):
        notifier = MagicMock()
        engine = NotificationEngine(notifier)
        position = _make_position()
        engine.notify_position_opened(position)

        msg = notifier.notify.call_args[0][0]
        assert "Opened" in msg.title
        assert "BTC" in msg.body

    def test_position_closed_notification(self):
        notifier = MagicMock()
        engine = NotificationEngine(notifier)
        position = _make_position()
        engine.notify_position_closed(position, 20.0)

        msg = notifier.notify.call_args[0][0]
        assert "Closed" in msg.title
        assert "20.00" in msg.body

    def test_duplicate_signal_protection(self):
        notifier = MagicMock()
        engine = NotificationEngine(notifier)
        signal = _make_signal()
        engine.notify_signal(signal)
        engine.notify_signal(signal)

        assert notifier.notify.call_count == 1

    def test_dispatcher_failure_does_not_crash(self):
        notifier = MagicMock()
        notifier.notify.side_effect = Exception("Telegram API down")
        engine = NotificationEngine(notifier)
        signal = _make_signal()

        engine.notify_signal(signal)  # Should not raise