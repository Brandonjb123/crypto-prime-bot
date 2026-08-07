"""Unit tests untuk BinanceFuturesAdapter."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.core.models.execution import ExecutionPlan
from src.core.types.enums import (
    ExchangeErrorType,
    ExecutionAction,
    ExecutionStatus,
    ExecutionType,
    OrderRejectReason,
    OrderStatus,
    RecommendationAction,
    Side,
)
from src.exchange.adapters.binance.binance_futures_adapter import BinanceFuturesAdapter
from src.exchange.adapters.binance.client import BinanceClient
from src.exchange.adapters.binance.exceptions import BinanceAPIError


def _make_plan(status=ExecutionStatus.READY):
    return ExecutionPlan(
        execution_id=uuid4(),
        action=ExecutionAction.PLACE_ORDER,
        status=status,
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


def _make_plan_short():
    """Buat plan dengan side=SHORT."""
    plan = _make_plan()
    return ExecutionPlan(
        execution_id=plan.execution_id,
        action=plan.action,
        status=plan.status,
        execution_type=plan.execution_type,
        side=Side.SHORT,
        entry_price=plan.entry_price,
        stop_loss=plan.stop_loss,
        take_profit=plan.take_profit,
        position_size=plan.position_size,
        risk_reward_ratio=plan.risk_reward_ratio,
        confidence_score=plan.confidence_score,
        recommendation_action=plan.recommendation_action,
        summary=plan.summary,
        blocked_reasons=plan.blocked_reasons,
        validation_reasons=plan.validation_reasons,
        warnings=plan.warnings,
        timestamp=plan.timestamp,
    )


class TestBinanceFuturesAdapter:
    async def test_buy_order_success(self):
        client = MagicMock(spec=BinanceClient)
        client.place_order = AsyncMock(
            return_value={
                "orderId": "12345678-1234-5678-1234-567812345678",
                "status": "FILLED",
                "side": "BUY",
                "price": "50000.00",
                "avgPrice": "50000.00",
                "origQty": "0.100",
                "type": "MARKET",
                "symbol": "BTCUSDT",
            }
        )
        adapter = BinanceFuturesAdapter(client)
        plan = _make_plan()
        result = await adapter.place_order(plan)
        assert result.status == OrderStatus.FILLED
        assert result.side == Side.LONG

    async def test_sell_order_success(self):
        client = MagicMock(spec=BinanceClient)
        client.place_order = AsyncMock(
            return_value={
                "orderId": "12345678-1234-5678-1234-567812345678",
                "status": "FILLED",
                "side": "SELL",
                "price": "50000.00",
                "avgPrice": "50000.00",
                "origQty": "0.100",
                "type": "MARKET",
                "symbol": "BTCUSDT",
            }
        )
        adapter = BinanceFuturesAdapter(client)
        plan = _make_plan_short()
        result = await adapter.place_order(plan)
        assert result.status == OrderStatus.FILLED
        assert result.side == Side.SHORT

    async def test_rejected_order(self):
        client = MagicMock(spec=BinanceClient)
        client.place_order = AsyncMock(
            return_value={
                "orderId": "12345678-1234-5678-1234-567812345678",
                "status": "REJECTED",
                "side": "BUY",
                "avgPrice": "0",
                "origQty": "0.100",
                "type": "MARKET",
                "symbol": "BTCUSDT",
            }
        )
        adapter = BinanceFuturesAdapter(client)
        plan = _make_plan()
        result = await adapter.place_order(plan)
        assert result.status == OrderStatus.REJECTED

    async def test_insufficient_balance(self):
        client = MagicMock(spec=BinanceClient)
        client.place_order = AsyncMock(
            side_effect=BinanceAPIError(
                "Insufficient balance", ExchangeErrorType.INSUFFICIENT_BALANCE
            )
        )
        adapter = BinanceFuturesAdapter(client)
        plan = _make_plan()
        result = await adapter.place_order(plan)
        assert result.status == OrderStatus.REJECTED
        assert result.reject_reason == OrderRejectReason.INSUFFICIENT_BALANCE

    async def test_network_error(self):
        client = MagicMock(spec=BinanceClient)
        client.place_order = AsyncMock(
            side_effect=BinanceAPIError("Network error", ExchangeErrorType.NETWORK_ERROR)
        )
        adapter = BinanceFuturesAdapter(client)
        plan = _make_plan()
        result = await adapter.place_order(plan)
        assert result.status == OrderStatus.REJECTED
        assert result.reject_reason == OrderRejectReason.UNKNOWN

    async def test_auth_error(self):
        client = MagicMock(spec=BinanceClient)
        client.place_order = AsyncMock(
            side_effect=BinanceAPIError("Auth error", ExchangeErrorType.AUTH_ERROR)
        )
        adapter = BinanceFuturesAdapter(client)
        plan = _make_plan()
        result = await adapter.place_order(plan)
        assert result.status == OrderStatus.REJECTED
        assert result.reject_reason == OrderRejectReason.UNKNOWN

    async def test_blocked_plan(self):
        client = MagicMock(spec=BinanceClient)
        adapter = BinanceFuturesAdapter(client)
        plan = _make_plan(ExecutionStatus.BLOCKED)
        result = await adapter.place_order(plan)
        assert result.status == OrderStatus.REJECTED

    async def test_deterministic_mock(self):
        client = MagicMock(spec=BinanceClient)
        client.place_order = AsyncMock(
            return_value={
                "orderId": "12345678-1234-5678-1234-567812345678",
                "status": "FILLED",
                "side": "BUY",
                "price": "50000.00",
                "avgPrice": "50000.00",
                "origQty": "0.100",
                "type": "MARKET",
                "symbol": "BTCUSDT",
            }
        )
        adapter1 = BinanceFuturesAdapter(client)
        adapter2 = BinanceFuturesAdapter(client)
        plan = _make_plan()
        r1 = await adapter1.place_order(plan)
        r2 = await adapter2.place_order(plan)
        assert r1.status == r2.status
        assert r1.side == r2.side
