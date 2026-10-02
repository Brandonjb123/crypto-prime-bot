"""Phase B Step 5 tests — per-position metrics projection + formatter."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.position import Position
from src.core.types.enums import (
    PositionCloseReason,
    PositionStatus,
    Side,
)
from src.telegram.formatter import format_positions_card
from src.telegram.use_cases import read_positions_with_metrics

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
    tp: float = 110.0,
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
        take_profit=tp,
        tp1_price=tp * 0.95,
        tp2_price=tp,
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


# ---------- read_positions_with_metrics ----------


class TestReadPositionsWithMetrics:
    def test_empty_ctx(self) -> None:
        assert read_positions_with_metrics(None) == []
        assert read_positions_with_metrics({}) == []

    def test_no_positions(self) -> None:
        ctx = {"positions": [], "price_provider": _FakeProvider()}
        assert read_positions_with_metrics(ctx) == []

    def test_projection_has_expected_keys(self) -> None:
        pos = _make_position()
        provider = _FakeProvider({"BTC": 105.0})
        ctx = {"positions": [pos], "price_provider": provider}

        out = read_positions_with_metrics(ctx)
        assert len(out) == 1
        item = out[0]
        assert item["position"] is pos
        assert item["current_price"] == 105.0
        assert item["unrealized_pnl"] == 5.0  # (105 - 100) * 1
        assert item["progress_pct"] == 50.0   # (105-100)/(110-100)*100

    def test_missing_price_returns_none_metrics(self) -> None:
        pos = _make_position(symbol="ZZZ")
        provider = _FakeProvider({})
        ctx = {"positions": [pos], "price_provider": provider}

        out = read_positions_with_metrics(ctx)
        assert out[0]["current_price"] is None
        assert out[0]["unrealized_pnl"] is None
        assert out[0]["progress_pct"] is None

    def test_no_provider_returns_none_metrics(self) -> None:
        pos = _make_position()
        ctx = {"positions": [pos]}  # no price_provider

        out = read_positions_with_metrics(ctx)
        assert out[0]["current_price"] is None
        assert out[0]["unrealized_pnl"] is None
        assert out[0]["progress_pct"] is None


# ---------- progress formula ----------


class TestProgressFormula:
    def _progress(self, side, entry, tp, current):
        pos = _make_position(side=side, entry=entry, tp=tp)
        provider = _FakeProvider({pos.symbol: current})
        ctx = {"positions": [pos], "price_provider": provider}
        return read_positions_with_metrics(ctx)[0]["progress_pct"]

    def test_long_entry_is_zero(self) -> None:
        assert self._progress(Side.LONG, 100.0, 110.0, 100.0) == 0.0

    def test_long_halfway_is_50(self) -> None:
        assert self._progress(Side.LONG, 100.0, 110.0, 105.0) == 50.0

    def test_long_at_tp_is_100(self) -> None:
        assert self._progress(Side.LONG, 100.0, 110.0, 110.0) == 100.0

    def test_long_beyond_tp_clamps_100(self) -> None:
        assert self._progress(Side.LONG, 100.0, 110.0, 120.0) == 100.0

    def test_long_adverse_clamps_zero(self) -> None:
        assert self._progress(Side.LONG, 100.0, 110.0, 90.0) == 0.0

    def test_short_entry_is_zero(self) -> None:
        assert self._progress(Side.SHORT, 100.0, 90.0, 100.0) == 0.0

    def test_short_halfway_is_50(self) -> None:
        assert self._progress(Side.SHORT, 100.0, 90.0, 95.0) == 50.0

    def test_short_at_tp_is_100(self) -> None:
        assert self._progress(Side.SHORT, 100.0, 90.0, 90.0) == 100.0

    def test_short_beyond_tp_clamps_100(self) -> None:
        assert self._progress(Side.SHORT, 100.0, 90.0, 80.0) == 100.0

    def test_short_adverse_clamps_zero(self) -> None:
        assert self._progress(Side.SHORT, 100.0, 90.0, 110.0) == 0.0

    def test_missing_current_price_is_none(self) -> None:
        pos = _make_position(entry=100.0, tp=110.0)
        provider = _FakeProvider({})
        ctx = {"positions": [pos], "price_provider": provider}
        assert read_positions_with_metrics(ctx)[0]["progress_pct"] is None

    def test_missing_tp_is_none(self) -> None:
        pos = _make_position(entry=100.0, tp=0.0)
        provider = _FakeProvider({pos.symbol: 105.0})
        ctx = {"positions": [pos], "price_provider": provider}
        assert read_positions_with_metrics(ctx)[0]["progress_pct"] is None

    def test_entry_equals_tp_returns_none(self) -> None:
        pos = _make_position(entry=100.0, tp=100.0)
        provider = _FakeProvider({pos.symbol: 105.0})
        ctx = {"positions": [pos], "price_provider": provider}
        assert read_positions_with_metrics(ctx)[0]["progress_pct"] is None


# ---------- formatter ----------


class TestFormatterWithMetrics:
    def test_card_with_metrics_shows_current_pnl_progress(self) -> None:
        pos = _make_position(entry=100.0, tp=110.0)
        metrics_map = {
            pos.position_id: {
                "position": pos,
                "current_price": 105.0,
                "unrealized_pnl": 5.0,
                "progress_pct": 50.0,
            }
        }
        out = format_positions_card([pos], metrics_map=metrics_map)
        assert "Current:" in out
        assert "105.00" in out
        assert "PnL:" in out
        assert "5.00" in out
        assert "Progress to TP:" in out
        assert "50.0%" in out

    def test_card_with_metrics_na_when_missing(self) -> None:
        pos = _make_position()
        metrics_map = {
            pos.position_id: {
                "position": pos,
                "current_price": None,
                "unrealized_pnl": None,
                "progress_pct": None,
            }
        }
        out = format_positions_card([pos], metrics_map=metrics_map)
        # 3 N/A's: current, pnl, progress
        assert out.count("N/A") == 3

    def test_card_without_metrics_backward_compatible(self) -> None:
        pos = _make_position()
        old_out = format_positions_card([pos])
        # tidak ada metrics
        assert "Current:" not in old_out
        assert "PnL:" not in old_out
        assert "Progress" not in old_out
        # field lama tetap
        assert "Entry" in old_out
        assert "SL" in old_out
        assert "TP" in old_out
        assert "Status" in old_out

    def test_empty_positions_unchanged(self) -> None:
        assert format_positions_card([]) == format_positions_card([], metrics_map=None)
        assert "Belum ada posisi" in format_positions_card([])