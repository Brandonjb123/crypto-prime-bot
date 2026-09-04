"""Integration test: PositionManager → PortfolioManager → PortfolioSnapshot (with Live Price)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.core.models.account import AccountSnapshot
from src.core.models.order import OrderResult
from src.core.models.portfolio import PortfolioSnapshot
from src.core.types.enums import (
    ExecutionType,
    OrderRejectReason,
    OrderStatus,
    PortfolioStatus,
    Side,
)
from src.market.in_memory_price_provider import InMemoryPriceProvider
from src.portfolio.portfolio_manager import PortfolioManager
from src.position.position_manager import PositionManager


class TestPortfolioPipeline:
    def test_positions_to_portfolio(self):
        order1 = OrderResult(
            execution_id=uuid4(),
            order_id=uuid4(),
            status=OrderStatus.FILLED,
            reject_reason=OrderRejectReason.NONE,
            execution_type=ExecutionType.MARKET,
            side=Side.LONG,
            symbol="BTC/USDT",
            requested_entry=50000.0,
            executed_entry=50000.0,
            position_size=0.1,
            stop_loss=48000.0,
            take_profit=55000.0,
            timestamp=datetime.now(UTC),
        )
        order2 = OrderResult(
            execution_id=uuid4(),
            order_id=uuid4(),
            status=OrderStatus.FILLED,
            reject_reason=OrderRejectReason.NONE,
            execution_type=ExecutionType.MARKET,
            side=Side.SHORT,
            symbol="ETH/USDT",
            requested_entry=3000.0,
            executed_entry=3000.0,
            position_size=0.2,
            stop_loss=3200.0,
            take_profit=2800.0,
            timestamp=datetime.now(UTC),
        )

        pm = PositionManager()
        pm.open_position(order1)
        pm.open_position(order2)

        provider = InMemoryPriceProvider()
        provider.update_price("BTC/USDT", 51000.0)
        provider.update_price("ETH/USDT", 2900.0)

        account = AccountSnapshot(
            balance=10000.0,
            equity=10000.0,
            margin_used=0.0,
            free_margin=10000.0,
            timestamp=datetime.now(UTC),
        )

        pf = PortfolioManager()
        snap = pf.create_snapshot(pm.get_all_positions(), account, provider)

        assert isinstance(snap, PortfolioSnapshot)
        assert snap.status == PortfolioStatus.ACTIVE
        assert snap.open_positions == 2
        assert snap.long_positions == 1
        assert snap.short_positions == 1
        assert snap.gross_exposure == pytest.approx(0.3)
        assert snap.net_exposure == -0.1  # 0.1 - 0.2
        # unrealized: LONG BTC (51000-50000)*0.1 = 100, SHORT ETH (3000-2900)*0.2 = 20 → total 120
        assert snap.unrealized_pnl == 120.0
        assert snap.equity == 10120.0  # 10000 + 0 + 120
