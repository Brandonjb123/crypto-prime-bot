from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.execution import ExecutionPlan
from src.core.types.enums import (
    ExecutionAction,
    ExecutionStatus,
    ExecutionType,
    OrderRejectReason,
    OrderStatus,
    RecommendationAction,
)
from src.exchange.adapters.paper import PaperExchangeAdapter
from src.exchange.executor import OrderExecutor


def _make_plan(status=ExecutionStatus.READY):
    return ExecutionPlan(
        execution_id=uuid4(),
        action=ExecutionAction.PLACE_ORDER
        if status == ExecutionStatus.READY
        else ExecutionAction.DO_NOT_EXECUTE,
        status=status,
        execution_type=ExecutionType.MARKET,
        side=None,
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


class TestOrderExecutor:
    async def test_ready_calls_adapter(self):
        class TrackingAdapter(PaperExchangeAdapter):
            called = False

            async def place_order(self, plan):
                self.called = True
                return await super().place_order(plan)

        adapter = TrackingAdapter()
        executor = OrderExecutor(adapter)
        result = await executor.execute(_make_plan(ExecutionStatus.READY))
        assert adapter.called is True
        assert result.status == OrderStatus.FILLED

    async def test_blocked_does_not_call_adapter(self):
        class TrackingAdapter(PaperExchangeAdapter):
            called = False

            async def place_order(self, plan):
                self.called = True
                return await super().place_order(plan)

        adapter = TrackingAdapter()
        executor = OrderExecutor(adapter)
        result = await executor.execute(_make_plan(ExecutionStatus.BLOCKED))
        assert adapter.called is False
        assert result.status == OrderStatus.REJECTED

    async def test_uuid_preserved(self):
        executor = OrderExecutor(PaperExchangeAdapter())
        plan = _make_plan()
        result = await executor.execute(plan)
        assert result.execution_id == plan.execution_id
        assert isinstance(result.order_id, type(uuid4()))

    async def test_blocked_reject_reason(self):
        executor = OrderExecutor(PaperExchangeAdapter())
        result = await executor.execute(_make_plan(ExecutionStatus.BLOCKED))
        assert result.reject_reason == OrderRejectReason.UNKNOWN

    async def test_deterministic(self):
        executor = OrderExecutor(PaperExchangeAdapter())
        plan = _make_plan()
        r1 = await executor.execute(plan)
        r2 = await executor.execute(plan)
        assert r1.status == r2.status
