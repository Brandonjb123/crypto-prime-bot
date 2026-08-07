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


class TestPaperExchangeAdapter:
    async def test_ready_filled(self):
        adapter = PaperExchangeAdapter()
        result = await adapter.place_order(_make_plan(ExecutionStatus.READY))
        assert result.status == OrderStatus.FILLED
        assert result.reject_reason == OrderRejectReason.NONE
        assert result.executed_entry == 50000.0

    async def test_blocked_rejected(self):
        adapter = PaperExchangeAdapter()
        result = await adapter.place_order(_make_plan(ExecutionStatus.BLOCKED))
        assert result.status == OrderStatus.REJECTED
        assert result.reject_reason == OrderRejectReason.UNKNOWN
        assert result.executed_entry is None

    async def test_order_id_unique(self):
        adapter = PaperExchangeAdapter()
        r1 = await adapter.place_order(_make_plan())
        r2 = await adapter.place_order(_make_plan())
        assert r1.order_id != r2.order_id

    async def test_deterministic(self):
        adapter = PaperExchangeAdapter()
        plan = _make_plan()
        r1 = await adapter.place_order(plan)
        r2 = await adapter.place_order(plan)
        assert r1.status == r2.status
        assert r1.executed_entry == r2.executed_entry
