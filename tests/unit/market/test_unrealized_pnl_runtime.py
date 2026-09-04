from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.position import Position
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.market.in_memory_price_provider import InMemoryPriceProvider
from src.market.pnl_engine import calculate_unrealized


def _make_open_long(symbol="BTC", entry=79000.0, size=0.01):
    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        symbol=symbol,
        side=Side.LONG,
        status=PositionStatus.OPEN,
        entry_price=entry,
        stop_loss=entry - 1000,
        take_profit=entry + 2000,
        position_size=size,
        opened_at=datetime.now(UTC),
        closed_at=None,
        close_reason=PositionCloseReason.NONE,
        last_price=entry,
        last_updated=datetime.now(UTC),
    )


def test_unrealized_pnl_positive_for_matching_symbol():
    provider = InMemoryPriceProvider()
    provider.update_price("BTC", 80000.0)

    pos = _make_open_long(symbol="BTC", entry=79000.0, size=0.01)
    pnl = calculate_unrealized([pos], provider)

    assert pnl > 0, f"Expected positive unrealized PnL, got {pnl}"


def test_unrealized_pnl_positive_with_symbol_suffix():
    provider = InMemoryPriceProvider()
    provider.update_price("BTC/USDT", 80000.0)

    pos = _make_open_long(symbol="BTC", entry=79000.0, size=0.01)
    pnl = calculate_unrealized([pos], provider)

    assert pnl > 0, f"Expected positive unrealized PnL with suffix normalization, got {pnl}"