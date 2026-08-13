"""Unit tests untuk partial fill mapping."""

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


def _make_plan():
    return ExecutionPlan(
        execution_id=uuid4(),
        action=ExecutionAction.PLACE_ORDER,
        status=ExecutionStatus.READY,
        execution_type=ExecutionType.MARKET,
        side=Side.LONG,
        entry_price=50000.0,
        stop_loss=48000.0,
        take_profit=55000.0,
        position_size=1.0,
        risk_reward_ratio=2.5,
        confidence_score=0.85,
        recommendation_action=RecommendationAction.BUY,
        summary="Partial fill test",
        blocked_reasons=[],
        validation_reasons=[],
        warnings=[],
        timestamp=datetime.now(UTC),
        client_order_id="test-client-oid",
    )


class TestBinanceFuturesAdapterPartialFill:
    async def test_zero_fill(self):
        client = MagicMock()
        client.place_order = AsyncMock(return_value={
            "orderId": "1",
            "status": "NEW",
            "symbol": "BTCUSDT",
            "origQty": "1.0",
            "executedQty": "0",
            "avgPrice": "0",
        })
        adapter = BinanceFuturesAdapter(client)
        result = await adapter.place_order(_make_plan())
        assert result.status == OrderStatus.NEW
        assert result.requested_quantity == 1.0
        assert result.filled_quantity == 0.0
        assert result.remaining_quantity == 1.0

    async def test_partial_fill(self):
        client = MagicMock()
        client.place_order = AsyncMock(return_value={
            "orderId": "1",
            "status": "PARTIALLY_FILLED",
            "symbol": "BTCUSDT",
            "origQty": "1.0",
            "executedQty": "0.4",
            "avgPrice": "49950.0",
        })
        adapter = BinanceFuturesAdapter(client)
        result = await adapter.place_order(_make_plan())
        assert result.status == OrderStatus.PARTIALLY_FILLED
        assert result.filled_quantity == 0.4
        assert result.remaining_quantity == 0.6
        assert result.average_fill_price == 49950.0
        assert result.position_size == 0.4

    async def test_full_fill(self):
        client = MagicMock()
        client.place_order = AsyncMock(return_value={
            "orderId": "1",
            "status": "FILLED",
            "symbol": "BTCUSDT",
            "origQty": "1.0",
            "executedQty": "1.0",
            "avgPrice": "50000.0",
        })
        adapter = BinanceFuturesAdapter(client)
        result = await adapter.place_order(_make_plan())
        assert result.status == OrderStatus.FILLED
        assert result.filled_quantity == 1.0
        assert result.remaining_quantity == 0.0
        assert result.position_size == 1.0  