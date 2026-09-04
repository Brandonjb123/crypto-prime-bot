"""Integration test: ExecutionPlan → Order Executor → OrderResult."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.execution import ExecutionPlan
from src.core.types.enums import (
    ExecutionAction,
    ExecutionStatus,
    ExecutionType,
    OrderStatus,
    RecommendationAction,
)
from src.exchange.adapters.paper import PaperExchangeAdapter
from src.exchange.executor import OrderExecutor


class TestExchangePipeline:
    async def test_execution_to_order(self):
        plan = ExecutionPlan(
            execution_id=uuid4(),
            action=ExecutionAction.PLACE_ORDER,
            status=ExecutionStatus.READY,
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
        executor = OrderExecutor(PaperExchangeAdapter())
        result = await executor.execute(plan)
        assert result.status == OrderStatus.FILLED
        assert result.execution_id == plan.execution_id
