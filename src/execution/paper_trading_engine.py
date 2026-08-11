"""Paper Trading Engine — simulasi eksekusi 100% deterministic."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.core.models.execution_result import ExecutionResult
from src.core.models.trading_signal import TradingSignal
from src.logging.logger import get_logger
from src.notification.notification_engine import NotificationEngine
from src.portfolio.portfolio_state_manager import PortfolioStateManager
from src.storage.adapters.in_memory_execution_repository import InMemoryExecutionRepository

logger = get_logger("paper_trading_engine")


class PaperTradingEngine:
    def __init__(
        self,
        portfolio_manager: PortfolioStateManager,
        execution_repo: InMemoryExecutionRepository | None = None,
        notification_engine: NotificationEngine | None = None,
        slippage: float = 0.0,
    ):
        self.portfolio_manager = portfolio_manager
        self.execution_repo = execution_repo or InMemoryExecutionRepository()
        self.notification_engine = notification_engine
        self.slippage = slippage

    def execute(self, signal: TradingSignal) -> ExecutionResult:
        # Cegah eksekusi duplikat
        if self.execution_repo.exists_by_signal_id(signal.signal_id):
            logger.warning(f"Signal {signal.signal_id} already executed")
            return ExecutionResult(
                execution_id=uuid4(),
                signal_id=signal.signal_id,
                symbol=signal.symbol,
                side=signal.side,
                status="REJECTED",
                requested_price=signal.entry_price or 0.0,
                position_size=signal.position_size,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                slippage=0.0,
                timestamp=datetime.now(UTC),
            )

        # Hanya proses sinyal ACTIVE
        if signal.status != "ACTIVE":
            status = "SKIPPED" if signal.status == "SKIPPED" else "REJECTED"
            result = ExecutionResult(
                execution_id=uuid4(),
                signal_id=signal.signal_id,
                symbol=signal.symbol,
                side=signal.side,
                status=status,
                requested_price=signal.entry_price or 0.0,
                position_size=signal.position_size,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                slippage=0.0,
                timestamp=datetime.now(UTC),
            )
            self.execution_repo.save(result)
            return result

        # Hitung harga eksekusi deterministik dengan slippage
        if signal.side == "BUY":
            executed_price = (signal.entry_price or 0.0) + self.slippage
        else:
            executed_price = (signal.entry_price or 0.0) - self.slippage

        result = ExecutionResult(
            execution_id=uuid4(),
            signal_id=signal.signal_id,
            symbol=signal.symbol,
            side=signal.side,
            status="FILLED",
            requested_price=signal.entry_price or 0.0,
            executed_price=executed_price,
            position_size=signal.position_size,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            slippage=self.slippage,
            timestamp=datetime.now(UTC),
        )
        self.execution_repo.save(result)

        # Buka posisi di portfolio
        if result.status == "FILLED":
            position = self.portfolio_manager.open_position(signal)
            if position and self.notification_engine:
                self.notification_engine.notify_position_opened(position)
                # Notifikasi paper trade
                self._notify_paper_execution(result)

        return result

    def close_position(self, position_id: UUID, exit_price: float):
        pos = self.portfolio_manager.close_position(position_id, exit_price)
        if pos and self.notification_engine:
            if pos.side == "LONG":
                pnl = (exit_price - pos.entry_price) * pos.position_size
            else:
                pnl = (pos.entry_price - exit_price) * pos.position_size
            self.notification_engine.notify_position_closed(pos, pnl)
        return pos

    def _notify_paper_execution(self, result: ExecutionResult) -> None:
        """Kirim notifikasi eksekusi paper trading."""
        if not self.notification_engine:
            return
        # Gunakan notifier langsung (kita akan tambahkan method di NotificationEngine jika belum ada)
        from datetime import UTC, datetime

        from src.core.models.notification import NotificationMessage
        from src.core.types.enums import NotificationLevel

        msg = NotificationMessage(
            message_id=uuid4(),
            title="📝 Paper Trade Executed",
            body=(
                f"Symbol: {result.symbol}\n"
                f"Side: {result.side}\n"
                f"Entry: {result.executed_price:.2f}\n"
                f"Position Size: {result.position_size}\n"
                f"SL: {result.stop_loss:.2f}\n"
                f"TP: {result.take_profit:.2f}\n\n"
                f"Status: {result.status}\n"
                f"Mode: PAPER"
            ),
            level=NotificationLevel.INFO,
            timestamp=datetime.now(UTC),
        )
        try:
            self.notification_engine.notifier.notify(msg)
        except Exception as e:
            logger.error(f"Failed to send paper execution notification: {e}")