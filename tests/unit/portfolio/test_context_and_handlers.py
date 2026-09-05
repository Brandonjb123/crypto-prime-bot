from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.position import Position
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.portfolio.portfolio_state_manager import PortfolioStateManager
from src.telegram.command_handler import history_handler, trackrecord_handler


def _make_closed_position(symbol="BTC", pnl=100.0):
    entry = 50000.0
    size = 0.01
    exit_price = entry + (pnl / size)

    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        symbol=symbol,
        side=Side.LONG,
        status=PositionStatus.CLOSED,
        entry_price=entry,
        stop_loss=49000.0,
        take_profit=52000.0,
        position_size=size,
        opened_at=datetime.now(UTC),
        closed_at=datetime.now(UTC),
        close_reason=PositionCloseReason.TAKE_PROFIT,
        last_price=exit_price,
        last_updated=datetime.now(UTC),
    )


def test_get_context_returns_closed_positions():
    pm = PortfolioStateManager(initial_balance=10000.0)
    # Buka posisi lalu close untuk memunculkan closed
    pos = _make_closed_position()
    pm.repo.save(pos)

    ctx = pm.get_context()
    assert "closed_positions" in ctx
    assert len(ctx["closed_positions"]) == 1


def test_history_handler_sees_closed_positions():
    ctx = {
        "closed_positions": [_make_closed_position()],
    }
    resp = history_handler(None, ctx)
    assert "Belum ada closed trade" not in resp.text
    assert "BTC" in resp.text


def test_trackrecord_handler_counts_closed_positions():
    ctx = {
        "closed_positions": [_make_closed_position(pnl=150.0)],
    }
    resp = trackrecord_handler(None, ctx)
    assert "Closed trades: 1" in resp.text
    assert "Wins: 1" in resp.text
    assert "Total PnL: $150.00" in resp.text