"""Notification Engine — mengubah TradingSignal dan Portfolio Event menjadi NotificationMessage."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.notification import NotificationMessage
from src.core.models.position import Position
from src.core.models.trading_signal import TradingSignal
from src.core.types.enums import NotificationLevel
from src.logging.logger import get_logger
from src.notification.base_notifier import BaseNotifier

logger = get_logger("notification_engine")


class NotificationEngine:
    def __init__(self, notifier: BaseNotifier):
        self.notifier = notifier
        self._sent_signal_ids: set[str] = set()
        self._sent_position_ids: set[str] = set()

    def notify_signal(self, signal: TradingSignal) -> None:
        """Buat dan kirim notifikasi untuk TradingSignal."""
        signal_key = str(signal.signal_id)

        if signal_key in self._sent_signal_ids:
            logger.debug(f"Notification for signal {signal.signal_id} already sent")
            return

        logger.info("Creating notification for signal...")

        if signal.status == "ACTIVE":
            title = "🚨 Trading Signal"
            body = self._format_active_signal(signal)
            level = NotificationLevel.INFO
        elif signal.status == "SKIPPED":
            title = "⏭️ Signal Skipped"
            body = f"Signal {signal.signal_id} for {signal.symbol} was skipped.\nReason: WAIT decision"
            level = NotificationLevel.WARNING
        elif signal.status == "INVALID":
            title = "⚠️ Invalid Trading Signal"
            body = f"Signal {signal.signal_id} for {signal.symbol} is INVALID.\nStatus: INVALID"
            level = NotificationLevel.ERROR
        else:
            return

        message = NotificationMessage(
            message_id=uuid4(),
            title=title,
            body=body,
            level=level,
            timestamp=datetime.now(UTC),
        )

        self._send(message, signal_key)
        self._sent_signal_ids.add(signal_key)

    def notify_position_opened(self, position: Position) -> None:
        """Kirim notifikasi posisi dibuka."""
        pos_key = str(position.position_id)

        if pos_key in self._sent_position_ids:
            return

        title = "📈 Position Opened"
        side = "LONG" if position.side.value == "LONG" else "SHORT"
        body = (
            f"Symbol: {position.symbol}\n"
            f"Side: {side}\n"
            f"Entry: {position.entry_price:.2f}\n"
            f"Position Size: {position.position_size}\n"
            f"Stop Loss: {position.stop_loss:.2f}\n"
            f"Take Profit: {position.take_profit:.2f}"
        )

        message = NotificationMessage(
            message_id=uuid4(),
            title=title,
            body=body,
            level=NotificationLevel.INFO,
            timestamp=datetime.now(UTC),
        )

        self._send(message, pos_key)
        self._sent_position_ids.add(pos_key)

    def notify_position_closed(self, position: Position, realized_pnl: float) -> None:
        """Kirim notifikasi posisi ditutup."""
        pos_key = str(position.position_id)

        if pos_key in self._sent_position_ids:
            return

        title = "📉 Position Closed"
        side = "LONG" if position.side.value == "LONG" else "SHORT"
        pnl_emoji = "🟢" if realized_pnl >= 0 else "🔴"
        exit_price = position.entry_price + realized_pnl / position.position_size if position.position_size else position.entry_price
        body = (
            f"Symbol: {position.symbol}\n"
            f"Side: {side}\n"
            f"Entry: {position.entry_price:.2f}\n"
            f"Exit: {exit_price:.2f}\n"
            f"Position Size: {position.position_size}\n"
            f"Realized PnL: {pnl_emoji} {realized_pnl:.2f}"
        )

        message = NotificationMessage(
            message_id=uuid4(),
            title=title,
            body=body,
            level=NotificationLevel.INFO,
            timestamp=datetime.now(UTC),
        )

        self._send(message, pos_key)

    def _format_active_signal(self, signal: TradingSignal) -> str:
        """Format sinyal aktif untuk Telegram."""
        reasoning_lines = "\n".join(f"  • {r}" for r in signal.reasoning) if signal.reasoning else "  • No reasoning provided"

        return (
            f"Symbol: {signal.symbol}\n"
            f"Side: {signal.side}\n"
            f"Entry: {signal.entry_price:.2f}\n"
            f"Stop Loss: {signal.stop_loss:.2f}\n"
            f"Take Profit: {signal.take_profit:.2f}\n"
            f"Position Size: {signal.position_size}\n"
            f"Risk: {signal.risk_percent:.1f}%\n"
            f"Confidence: {signal.confidence}%\n"
            f"Risk Level: {signal.risk_level}\n\n"
            f"Reason:\n{reasoning_lines}"
        )

    def _send(self, message: NotificationMessage, dedup_key: str) -> None:
        """Kirim notifikasi dengan error handling."""
        try:
            logger.info("Dispatching notification...")
            self.notifier.notify(message)
            logger.info("Notification dispatched")
        except Exception as e:
            logger.error(f"Notification dispatch failed: {e}")