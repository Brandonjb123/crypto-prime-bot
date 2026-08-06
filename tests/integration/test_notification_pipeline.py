"""Integration test: Domain Events → Notification Dispatcher."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.account import AccountSnapshot
from src.core.models.execution import ExecutionPlan
from src.core.models.order import OrderResult
from src.core.types.enums import (
    ExecutionAction,
    ExecutionStatus,
    ExecutionType,
    OrderRejectReason,
    OrderStatus,
    RecommendationAction,
    Side,
)
from src.events.event_bus import EventBus
from src.events.events.order_executed import OrderExecutedEvent
from src.events.events.portfolio_updated import PortfolioUpdatedEvent
from src.events.events.position_opened import PositionOpenedEvent
from src.exchange.adapters.paper import PaperExchangeAdapter
from src.exchange.executor import OrderExecutor
from src.market.in_memory_price_provider import InMemoryPriceProvider
from src.notification.console_notifier import ConsoleNotifier
from src.notification.dispatcher import NotificationDispatcher
from src.notification.formatters.order_formatter import OrderExecutedFormatter
from src.notification.formatters.portfolio_formatter import PortfolioUpdatedFormatter
from src.notification.formatters.position_formatter import (
    PositionOpenedFormatter,
)
from src.portfolio.portfolio_manager import PortfolioManager
from src.position.position_manager import PositionManager


class TestNotificationPipeline:
    async def test_order_event_to_notification(self, capsys):
        bus = EventBus()
        notifier = ConsoleNotifier()
        dispatcher = NotificationDispatcher(notifier)
        dispatcher.register(OrderExecutedEvent, OrderExecutedFormatter())
        bus.register("order_executed", dispatcher.dispatch)

        plan = ExecutionPlan(
            execution_id=uuid4(),
            action=ExecutionAction.PLACE_ORDER,
            status=ExecutionStatus.READY,
            execution_type=ExecutionType.MARKET,
            side=Side.LONG,
            entry_price=50000.0,
            stop_loss=48000.0,
            take_profit=55000.0,
            position_size=0.1,
            risk_reward_ratio=2.5,
            confidence_score=0.85,
            recommendation_action=RecommendationAction.BUY,
            summary="Test",
            blocked_reasons=[],
            validation_reasons=[],
            warnings=[],
            timestamp=datetime.now(UTC),
        )
        executor = OrderExecutor(PaperExchangeAdapter(), bus)
        await executor.execute(plan)

        captured = capsys.readouterr()
        assert "Order Executed" in captured.out

    def test_position_event_to_notification(self, capsys):
        bus = EventBus()
        notifier = ConsoleNotifier()
        dispatcher = NotificationDispatcher(notifier)
        dispatcher.register(PositionOpenedEvent, PositionOpenedFormatter())
        bus.register("position_opened", dispatcher.dispatch)

        order = OrderResult(
            execution_id=uuid4(), order_id=uuid4(),
            status=OrderStatus.FILLED, reject_reason=OrderRejectReason.NONE,
            execution_type=ExecutionType.MARKET, side=Side.LONG,
            symbol="BTC/USDT", requested_entry=50000.0, executed_entry=50000.0,
            position_size=0.1, stop_loss=48000.0, take_profit=55000.0,
            timestamp=datetime.now(UTC),
        )
        pm = PositionManager(event_bus=bus)
        pm.open_position(order)

        captured = capsys.readouterr()
        assert "Position Opened" in captured.out

    def test_portfolio_event_to_notification(self, capsys):
        bus = EventBus()
        notifier = ConsoleNotifier()
        dispatcher = NotificationDispatcher(notifier)
        dispatcher.register(PortfolioUpdatedEvent, PortfolioUpdatedFormatter())
        bus.register("portfolio_updated", dispatcher.dispatch)

        order = OrderResult(
            execution_id=uuid4(), order_id=uuid4(),
            status=OrderStatus.FILLED, reject_reason=OrderRejectReason.NONE,
            execution_type=ExecutionType.MARKET, side=Side.LONG,
            symbol="BTC/USDT", requested_entry=50000.0, executed_entry=50000.0,
            position_size=0.1, stop_loss=48000.0, take_profit=55000.0,
            timestamp=datetime.now(UTC),
        )
        pm = PositionManager()
        pm.open_position(order)

        account = AccountSnapshot(balance=10000.0, equity=10000.0, margin_used=0.0, free_margin=10000.0, timestamp=datetime.now(UTC))
        provider = InMemoryPriceProvider()
        provider.update_price("BTC/USDT", 50000.0)
        pf = PortfolioManager(event_bus=bus)
        pf.create_snapshot(pm.get_all_positions(), account, provider)

        captured = capsys.readouterr()
        assert "Portfolio Updated" in captured.out