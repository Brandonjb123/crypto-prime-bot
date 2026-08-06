"""Integration test: Domain Events pipeline."""

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
from src.portfolio.portfolio_manager import PortfolioManager
from src.position.position_manager import PositionManager


class TestEventPipeline:
    async def test_order_executed_event(self):
        bus = EventBus()
        received = []
        bus.register("order_executed", lambda e: received.append(e))

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
        result = await executor.execute(plan)

        assert result.status == OrderStatus.FILLED
        assert len(received) == 1
        assert isinstance(received[0], OrderExecutedEvent)

    def test_position_opened_event(self):
        bus = EventBus()
        received = []
        bus.register("position_opened", lambda e: received.append(e))

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

        assert len(received) == 1
        assert isinstance(received[0], PositionOpenedEvent)

    def test_portfolio_updated_event(self):
        bus = EventBus()
        received = []
        bus.register("portfolio_updated", lambda e: received.append(e))

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

        assert len(received) == 1
        assert isinstance(received[0], PortfolioUpdatedEvent)