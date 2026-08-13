"""Live Trading Engine — eksekusi via BaseExchangeAdapter."""

from datetime import UTC, datetime
from uuid import uuid4

from loguru import logger

from src.core.models.execution import ExecutionPlan
from src.core.models.live_order import LiveOrder
from src.core.models.order import OrderResult
from src.core.types.enums import (
    ExecutionAction,
    ExecutionStatus,
    ExecutionType,
    OrderRejectReason,
    OrderStatus,
    Side,
)
from src.exchange.base import BaseExchangeAdapter
from src.execution.base_execution_engine import BaseExecutionEngine
from src.execution.order_repository import OrderRepository
from src.execution.risk_gate import RiskGate


class LiveTradingEngine(BaseExecutionEngine):
    def __init__(
        self,
        exchange: BaseExchangeAdapter,
        order_repo: OrderRepository | None = None,
        risk_gate: RiskGate | None = None,
    ):
        self.exchange = exchange
        self.order_repo = order_repo or OrderRepository()
        self.risk_gate = risk_gate or RiskGate()

    async def execute(self, signal) -> OrderResult:
        now = datetime.now(UTC)

        # 1. Risk check
        if not self.risk_gate.check(signal):
            return OrderResult(
                execution_id=uuid4(),
                order_id=uuid4(),
                status=OrderStatus.REJECTED,
                reject_reason=OrderRejectReason.RISK_GATE,
                execution_type=ExecutionType.LIVE,
                side=Side.LONG if signal.side.upper() == "LONG" else Side.SHORT,
                symbol=signal.symbol,
                requested_entry=signal.entry_price,
                executed_entry=None,
                position_size=signal.position_size,
                stop_loss=getattr(signal, "stop_loss", 0.0),
                take_profit=getattr(signal, "take_profit", 0.0),
                timestamp=now,
            )

        # 2. Buat idempotent client_order_id
        client_oid = f"{signal.signal_id}_{signal.symbol}_{signal.side}"

        # 3. Cek idempotensi
        existing = self.order_repo.get_by_client_order_id(client_oid)
        if existing:
            logger.warning(f"Duplicate execution blocked: {client_oid}")
            return OrderResult(
                execution_id=existing.execution_id,
                order_id=uuid4(),
                status=existing.status,
                reject_reason=OrderRejectReason.UNKNOWN,
                execution_type=ExecutionType.LIVE,
                side=existing.side,
                symbol=existing.symbol,
                requested_entry=existing.requested_price,
                executed_entry=existing.average_fill_price,
                position_size=existing.quantity,
                stop_loss=signal.stop_loss if hasattr(signal, "stop_loss") else 0.0,
                take_profit=signal.take_profit if hasattr(signal, "take_profit") else 0.0,
                timestamp=now,
            )

        # 4. Build ExecutionPlan untuk adapter
        side = Side.LONG if signal.side.upper() == "LONG" else Side.SHORT
        plan = ExecutionPlan(
            execution_id=uuid4(),
            action=ExecutionAction.PLACE_ORDER,
            status=ExecutionStatus.READY,
            execution_type=ExecutionType.MARKET,
            side=side,
            entry_price=signal.entry_price,
            stop_loss=getattr(signal, "stop_loss", 0.0),
            take_profit=getattr(signal, "take_profit", 0.0),
            position_size=signal.position_size,
            risk_reward_ratio=0.0,
            confidence_score=0.0,
            recommendation_action="BUY" if side == Side.LONG else "SELL",
            summary="Live order",
            blocked_reasons=[],
            validation_reasons=[],
            warnings=[],
            timestamp=now,
            client_order_id=client_oid,
        )

        order = LiveOrder(
            execution_id=plan.execution_id,
            signal_id=signal.signal_id,
            client_order_id=client_oid,
            symbol=signal.symbol,
            side=side,
            quantity=plan.position_size,
            requested_price=plan.entry_price,
            status=OrderStatus.NEW,
            created_at=now,
            updated_at=now,
        )
        self.order_repo.save(order)

        # 5. Submit via adapter
        try:
            result = await self.exchange.place_order(plan)
        except TimeoutError:
            order.status = OrderStatus.UNKNOWN
            order.updated_at = datetime.now(UTC)
            self.order_repo.update(order)
            logger.error(f"Order {order.execution_id} timeout — marked UNKNOWN")
            return OrderResult(
                execution_id=order.execution_id,
                order_id=uuid4(),
                status=OrderStatus.UNKNOWN,
                reject_reason=OrderRejectReason.UNKNOWN,
                execution_type=ExecutionType.LIVE,
                side=side,
                symbol=signal.symbol,
                requested_entry=signal.entry_price,
                executed_entry=None,
                position_size=signal.position_size,
                stop_loss=getattr(signal, "stop_loss", 0.0),
                take_profit=getattr(signal, "take_profit", 0.0),
                timestamp=datetime.now(UTC),
            )
        except Exception as e:
            order.status = OrderStatus.FAILED
            order.updated_at = datetime.now(UTC)
            self.order_repo.update(order)
            logger.error(f"Order {order.execution_id} failed: {e}")
            return OrderResult(
                execution_id=order.execution_id,
                order_id=uuid4(),
                status=OrderStatus.FAILED,
                reject_reason=OrderRejectReason.UNKNOWN,
                execution_type=ExecutionType.LIVE,
                side=side,
                symbol=signal.symbol,
                requested_entry=signal.entry_price,
                executed_entry=None,
                position_size=signal.position_size,
                stop_loss=getattr(signal, "stop_loss", 0.0),
                take_profit=getattr(signal, "take_profit", 0.0),
                timestamp=datetime.now(UTC),
            )

        # 6. Update local order
        order.exchange_order_id = str(result.order_id)
        order.status = result.status
        if result.status == OrderStatus.PARTIALLY_FILLED:
            order.filled_quantity = result.filled_quantity
            order.average_fill_price = result.average_fill_price or plan.entry_price
            order.remaining_quantity = result.remaining_quantity
        elif result.status == OrderStatus.FILLED:
            order.filled_quantity = result.filled_quantity or order.quantity
            order.average_fill_price = result.average_fill_price or plan.entry_price
            order.remaining_quantity = 0.0
        else:
            order.filled_quantity = 0.0
            order.average_fill_price = None
            order.remaining_quantity = order.quantity
        order.updated_at = datetime.now(UTC)
        self.order_repo.update(order)

        # Buat ulang OrderResult dengan execution_id yang benar
        result = OrderResult(
            execution_id=order.execution_id,
            order_id=result.order_id,
            status=result.status,
            reject_reason=result.reject_reason,
            execution_type=result.execution_type,
            side=result.side,
            symbol=result.symbol,
            requested_entry=result.requested_entry,
            executed_entry=result.executed_entry,
            position_size=result.position_size,
            stop_loss=result.stop_loss,
            take_profit=result.take_profit,
            timestamp=result.timestamp,
        )

        return result

    async def cancel(self, execution_id: str) -> OrderResult:
        order = self.order_repo.get(execution_id)
        if not order:
            now = datetime.now(UTC)
            return OrderResult(
                execution_id=uuid4(),
                order_id=uuid4(),
                status=OrderStatus.FAILED,
                reject_reason=OrderRejectReason.UNKNOWN,
                execution_type=ExecutionType.LIVE,
                side=None,
                symbol="",
                requested_entry=0.0,
                executed_entry=None,
                position_size=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                timestamp=now,
            )
        if order.exchange_order_id:
            return await self.exchange.cancel_order(order.exchange_order_id)
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now(UTC)
        self.order_repo.update(order)
        now = datetime.now(UTC)
        return OrderResult(
            execution_id=order.execution_id,
            order_id=uuid4(),
            status=OrderStatus.CANCELLED,
            reject_reason=OrderRejectReason.UNKNOWN,
            execution_type=ExecutionType.LIVE,
            side=order.side,
            symbol=order.symbol,
            requested_entry=order.requested_price,
            executed_entry=order.average_fill_price,
            position_size=order.quantity,
            stop_loss=0.0,
            take_profit=0.0,
            timestamp=now,
        )

    async def get_status(self, execution_id: str) -> OrderResult:
        order = self.order_repo.get(execution_id)
        if not order:
            now = datetime.now(UTC)
            return OrderResult(
                execution_id=uuid4(),
                order_id=uuid4(),
                status=OrderStatus.FAILED,
                reject_reason=OrderRejectReason.UNKNOWN,
                execution_type=ExecutionType.LIVE,
                side=None,
                symbol="",
                requested_entry=0.0,
                executed_entry=None,
                position_size=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                timestamp=now,
            )
        if order.exchange_order_id:
            return await self.exchange.get_order(order.exchange_order_id)
        now = datetime.now(UTC)
        return OrderResult(
            execution_id=order.execution_id,
            order_id=uuid4(),
            status=order.status,
            reject_reason=OrderRejectReason.UNKNOWN,
            execution_type=ExecutionType.LIVE,
            side=order.side,
            symbol=order.symbol,
            requested_entry=order.requested_price,
            executed_entry=order.average_fill_price,
            position_size=order.quantity,
            stop_loss=0.0,
            take_profit=0.0,
            timestamp=now,
        )