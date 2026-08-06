"""Integration test: ExecutionPlan → BinanceFuturesAdapter (mock) → OrderResult."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.core.models.execution import ExecutionPlan
from src.core.types.enums import (
    ExecutionAction,
    ExecutionStatus,
    ExecutionType,
    OrderStatus,
    RecommendationAction,
    Side,
)
from src.exchange.adapters.binance.binance_futures_adapter import BinanceFuturesAdapter
from src.exchange.adapters.binance.client import BinanceClient
from src.exchange.executor import OrderExecutor


class TestBinanceExchangePipeline:
    async def test_execution_to_binance_order(self):
        client = MagicMock(spec=BinanceClient)
        client.place_order = AsyncMock(return_value={
            "orderId": "12345678-1234-5678-1234-567812345678",
            "status": "FILLED",
            "side": "BUY",
            "price": "50000.00",
            "avgPrice": "50000.00",
            "origQty": "0.100",
            "type": "MARKET",
            "symbol": "BTCUSDT",
        })
        adapter = BinanceFuturesAdapter(client)
        executor = OrderExecutor(adapter)

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
        result = await executor.execute(plan)
        assert result.status == OrderStatus.FILLED