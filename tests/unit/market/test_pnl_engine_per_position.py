"""Tests untuk calculate_position_unrealized — per-position PnL helper."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.position import Position
from src.core.types.enums import (
    PositionCloseReason,
    PositionStatus,
    Side,
)
from src.market.pnl_engine import (
    calculate_position_unrealized,
    calculate_unrealized,
)

# ---------- fixtures ----------


class _FakeProvider:
    def __init__(self, prices: dict | None = None) -> None:
        self._prices = prices or {}

    def get_price(self, symbol: str):
        return self._prices.get(symbol)


def _make_position(
    symbol: str = "BTC",
    side: Side = Side.LONG,
    status: PositionStatus = PositionStatus.OPEN,
    entry: float = 100.0,
    size: float = 1.0,
) -> Position:
    now = datetime.now(UTC)
    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        signal_id=uuid4(),
        symbol=symbol,
        side=side,
        status=status,
        entry_price=entry,
        stop_loss=entry * 0.9,
        take_profit=entry * 1.2,
        tp1_price=entry * 1.1,
        tp2_price=entry * 1.2,
        position_size=size,
        opened_at=now,
        closed_at=now if status == PositionStatus.CLOSED else None,
        close_reason=(
            PositionCloseReason.MANUAL
            if status == PositionStatus.CLOSED
            else PositionCloseReason.NONE
        ),
        last_price=entry,
        last_updated=now,
        realized_pnl=0.0,
    )


# ---------- per-position PnL ----------


class TestCalculatePositionUnrealized:
    def test_long_profit(self) -> None:
        pos = _make_position(side=Side.LONG, entry=100.0, size=1.0)
        provider = _FakeProvider({"BTC": 110.0})
        assert calculate_position_unrealized(pos, provider) == 10.0

    def test_long_loss(self) -> None:
        pos = _make_position(side=Side.LONG, entry=100.0, size=1.0)
        provider = _FakeProvider({"BTC": 90.0})
        assert calculate_position_unrealized(pos, provider) == -10.0

    def test_short_profit(self) -> None:
        pos = _make_position(side=Side.SHORT, entry=100.0, size=1.0)
        provider = _FakeProvider({"BTC": 90.0})
        assert calculate_position_unrealized(pos, provider) == 10.0

    def test_short_loss(self) -> None:
        pos = _make_position(side=Side.SHORT, entry=100.0, size=1.0)
        provider = _FakeProvider({"BTC": 110.0})
        assert calculate_position_unrealized(pos, provider) == -10.0

    def test_zero_pnl_at_entry(self) -> None:
        pos = _make_position(entry=100.0, size=1.0)
        provider = _FakeProvider({"BTC": 100.0})
        assert calculate_position_unrealized(pos, provider) == 0.0

    def test_missing_price_returns_none(self) -> None:
        pos = _make_position()
        provider = _FakeProvider({})  # empty
        assert calculate_position_unrealized(pos, provider) is None

    def test_closed_position_returns_none(self) -> None:
        pos = _make_position(status=PositionStatus.CLOSED)
        provider = _FakeProvider({"BTC": 110.0})
        assert calculate_position_unrealized(pos, provider) is None

    def test_zero_position_size_returns_zero(self) -> None:
        pos = _make_position(entry=100.0, size=0.0)
        provider = _FakeProvider({"BTC": 110.0})
        assert calculate_position_unrealized(pos, provider) == 0.0


# ---------- critical invariant ----------


class TestInvariantSumEqualsTotal:
    """sum(per-position PnL) == calculate_unrealized(positions, provider)."""

    def test_mixed_positions_sum_equals_total(self) -> None:
        positions = [
            # profitable LONG
            _make_position(symbol="BTC", side=Side.LONG, entry=100.0, size=1.0),
            # losing LONG
            _make_position(symbol="ETH", side=Side.LONG, entry=200.0, size=0.5),
            # profitable SHORT
            _make_position(symbol="SOL", side=Side.SHORT, entry=50.0, size=2.0),
            # losing SHORT
            _make_position(symbol="XRP", side=Side.SHORT, entry=1.0, size=100.0),
            # missing price → None
            _make_position(symbol="UNKNOWN", side=Side.LONG, entry=10.0, size=1.0),
            # CLOSED → None
            _make_position(
                symbol="ADA",
                side=Side.LONG,
                entry=1.0,
                size=1.0,
                status=PositionStatus.CLOSED,
            ),
        ]
        provider = _FakeProvider(
            {
                "BTC": 110.0,  # +10
                "ETH": 190.0,  # -5
                "SOL": 40.0,   # +20
                "XRP": 1.5,    # -50
                # UNKNOWN missing
                "ADA": 5.0,    # ignored (CLOSED)
            }
        )

        per_position_sum = 0.0
        for pos in positions:
            val = calculate_position_unrealized(pos, provider)
            if val is not None:
                per_position_sum += val

        total = calculate_unrealized(positions, provider)

        assert per_position_sum == total
        assert total == -25.0  # 10 - 5 + 20 - 50

    def test_empty_positions(self) -> None:
        provider = _FakeProvider({})
        assert calculate_unrealized([], provider) == 0.0

    def test_all_missing_price_sum_is_zero(self) -> None:
        positions = [
            _make_position(symbol="A"),
            _make_position(symbol="B"),
        ]
        provider = _FakeProvider({})  # all missing
        per_position = [
            calculate_position_unrealized(p, provider) for p in positions
        ]
        assert all(v is None for v in per_position)
        assert calculate_unrealized(positions, provider) == 0.0