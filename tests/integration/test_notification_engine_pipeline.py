"""Integration test: TradingSignal → NotificationEngine → Notifier."""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

from src.core.models.trading_signal import TradingSignal
from src.notification.notification_engine import NotificationEngine


class TestNotificationPipeline:
    def test_signal_to_notification_flow(self):
        notifier = MagicMock()
        engine = NotificationEngine(notifier)

        signal = TradingSignal(
            signal_id=uuid4(),
            symbol="ETH",
            side="BUY",
            status="ACTIVE",
            entry_price=3000.0,
            stop_loss=2800.0,
            take_profit=3500.0,
            position_size=0.1,
            risk_percent=2.0,
            confidence=80,
            risk_level="MEDIUM",
            reasoning=["Bullish breakout"],
            created_at=datetime.now(UTC),
        )

        engine.notify_signal(signal)

        assert notifier.notify.called
        msg = notifier.notify.call_args[0][0]
        assert msg.title == "🚨 Trading Signal"
        assert "ETH" in msg.body
        assert "BUY" in msg.body
        assert "3000" in msg.body
        assert "Bullish breakout" in msg.body