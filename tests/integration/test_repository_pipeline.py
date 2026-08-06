"""Integration test: PositionManager → Repository → Portfolio → Repository."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.account import AccountSnapshot
from src.core.models.order import OrderResult
from src.core.types.enums import (
    ExecutionType,
    OrderRejectReason,
    OrderStatus,
    Side,
)
from src.market.in_memory_price_provider import InMemoryPriceProvider
from src.portfolio.portfolio_manager import PortfolioManager
from src.position.position_manager import PositionManager
from src.storage.adapters.in_memory_portfolio_repository import InMemoryPortfolioRepository
from src.storage.adapters.in_memory_position_repository import InMemoryPositionRepository


class TestRepositoryPipeline:
    def test_position_to_repository(self):
        order = OrderResult(
            execution_id=uuid4(), order_id=uuid4(),
            status=OrderStatus.FILLED, reject_reason=OrderRejectReason.NONE,
            execution_type=ExecutionType.MARKET, side=Side.LONG,
            symbol="BTC/USDT", requested_entry=50000.0, executed_entry=50000.0,
            position_size=0.1, stop_loss=48000.0, take_profit=55000.0,
            timestamp=datetime.now(UTC),
        )
        pm = PositionManager()
        pos = pm.open_position(order)

        repo = InMemoryPositionRepository()
        repo.save(pos)
        assert repo.count() == 1
        assert repo.get_open()[0].symbol == "BTC/USDT"

    def test_portfolio_to_repository(self):
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
        pf = PortfolioManager()
        snap = pf.create_snapshot(pm.get_all_positions(), account, provider)

        repo = InMemoryPortfolioRepository()
        repo.save(snap)
        assert repo.count() == 1
        assert repo.latest().equity == 10000.0