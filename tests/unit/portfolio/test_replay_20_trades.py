from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.core.models.position import Position
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.portfolio.portfolio_state_manager import PortfolioStateManager

TRADES = [
    ("BTC", "LONG", 79209.36, 77152.01, -28.14),
    ("ETH", "LONG", 2626.01, 2547.17, -22.62),
    ("SOL", "LONG", 104.30, 101.07, -20.61),
    ("XRP", "LONG", 1.41, 1.36, -23.11),
    ("ETH", "LONG", 2547.17, 2448.86, -28.10),
    ("AVAX", "SHORT", 7.44, 7.90, -33.63),
    ("LINK", "SHORT", 11.52, 12.05, 29.17),
    ("XRP", "SHORT", 1.34, 1.39, -27.40),
    ("XRP", "LONG", 1.39, 1.28, 8.93),
    ("BTC", "LONG", 78074.00, 77040.01, -20.33),
    ("AVAX", "LONG", 7.58, 7.24, -34.67),
    ("SOL", "LONG", 103.42, 100.91, -21.18),
    ("ETH", "SHORT", 2435.23, 2513.85, -26.02),
    ("BTC", "SHORT", 75387.52, 76885.72, -21.51),
    ("BNB", "SHORT", 710.44, 725.60, -22.21),
    ("SOL", "SHORT", 96.76, 99.64, -20.10),
    ("ADA", "SHORT", 0.19, 0.21, -24.80),
    ("XRP", "SHORT", 1.29, 1.37, -27.93),
    ("SOL", "LONG", 101.26, 112.47, 44.63),
    ("AVAX", "LONG", 7.63, 8.60, 42.91),
]


def test_replay_20_trades_aggregate_matches_sum():
    pm = PortfolioStateManager(initial_balance=10000.0)

    for _i, (symbol, side, entry, exit_price, rpnl) in enumerate(TRADES):
        pos = Position(
            position_id=uuid4(),
            execution_id=uuid4(),
            order_id=uuid4(),
            symbol=symbol,
            side=Side.LONG if side == "LONG" else Side.SHORT,
            status=PositionStatus.CLOSED,
            entry_price=entry,
            stop_loss=entry * 0.95,
            take_profit=entry * 1.05,
            position_size=0.01,
            opened_at=datetime.now(UTC),
            closed_at=datetime.now(UTC),
            close_reason=PositionCloseReason.STOP_LOSS,
            last_price=exit_price,
            last_updated=datetime.now(UTC),
            realized_pnl=rpnl,
        )
        pm.repo.save(pos)

    state = pm.get_state()
    expected = sum(t[4] for t in TRADES)
    assert state.realized_pnl == pytest.approx(expected, abs=0.01)
    assert state.realized_pnl == pytest.approx(-276.72, abs=0.01)