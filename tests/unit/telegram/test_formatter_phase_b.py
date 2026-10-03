"""Phase B formatter tests — synthetic fixtures only.

Tidak menggunakan historical burn-in dataset.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.core.models.portfolio_state import PortfolioState
from src.core.models.position import Position
from src.core.models.trading_signal import TradingSignal
from src.core.types.enums import (
    PositionCloseReason,
    PositionStatus,
    Side,
)
from src.telegram.formatter import (
    format_history_card,
    format_portfolio_card,
    format_positions_card,
    format_signal_card,
    format_trackrecord_card,
)
from src.telegram.use_cases import TrackRecordSummary

# ---------- fixtures ----------


def _make_signal(
    symbol: str = "BTC",
    side: str = "BUY",
    status: str = "ACTIVE",
    reasoning: list | None = None,
) -> TradingSignal:
    return TradingSignal(
        signal_id=uuid4(),
        symbol=symbol,
        side=side,
        status=status,
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        take_profit_1=51000.0,
        take_profit_2=52000.0,
        position_size=0.01,
        risk_percent=1.0,
        confidence=80,
        risk_level="MEDIUM",
        reasoning=reasoning if reasoning is not None else ["Bullish momentum"],
        created_at=datetime(2026, 10, 2, 12, 0, tzinfo=UTC),
    )


def _make_position(
    symbol: str = "BTC",
    side: Side = Side.LONG,
    status: PositionStatus = PositionStatus.OPEN,
    realized_pnl: float = 0.0,
    duration_minutes: int = 0,
) -> Position:
    now = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
    closed_at = (
        now + timedelta(minutes=duration_minutes)
        if status == PositionStatus.CLOSED
        else None
    )
    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        signal_id=uuid4(),
        symbol=symbol,
        side=side,
        status=status,
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        tp1_price=51000.0,
        tp2_price=52000.0,
        position_size=0.01,
        opened_at=now,
        closed_at=closed_at,
        close_reason=(
            PositionCloseReason.MANUAL
            if status == PositionStatus.CLOSED
            else PositionCloseReason.NONE
        ),
        last_price=51000.0,
        last_updated=now,
        realized_pnl=realized_pnl,
    )


def _make_state(
    equity: float = 10100.0,
    realized: float = 100.0,
    unrealized: float = 0.0,
    total_pnl: float = 100.0,
) -> PortfolioState:
    return PortfolioState(
        account_balance=10000.0,
        equity=equity,
        realized_pnl=realized,
        unrealized_pnl=unrealized,
        total_pnl=total_pnl,
        open_positions=1,
        closed_positions=2,
        peak_equity=10100.0,
        drawdown=0.0,
        drawdown_percent=0.0,
        timestamp=datetime(2026, 10, 2, 12, 0, tzinfo=UTC),
    )


def _make_trackrecord(
    closed_count: int = 4,
    wins: int = 3,
    losses: int = 1,
    total_pnl: float = 150.0,
) -> TrackRecordSummary:
    average_pnl = total_pnl / closed_count if closed_count > 0 else 0.0
    win_rate = (wins / closed_count * 100) if closed_count > 0 else 0.0
    return TrackRecordSummary(
        closed_count=closed_count,
        wins=wins,
        losses=losses,
        total_pnl=total_pnl,
        average_pnl=average_pnl,
        win_rate=win_rate,
    )


# ---------- format_signal_card ----------


class TestSignalCard:
    def test_signal_card_active_contains_all_fields(self) -> None:
        sig = _make_signal()
        out = format_signal_card(sig)
        assert "BTC" in out
        assert "BUY" in out
        assert "ACTIVE" in out
        assert "$50,000.00" in out  # entry
        assert "$49,000.00" in out  # SL
        assert "$52,000.00" in out  # TP
        assert "80%" in out
        assert "MEDIUM" in out
        assert "2026-10-02" in out
        assert "Reasoning" in out

    def test_signal_card_preserves_reasoning_text(self) -> None:
        """Reasoning verbatim — tidak diparaphrase."""
        text = "RSI oversold with bullish divergence"
        sig = _make_signal(reasoning=[text])
        out = format_signal_card(sig)
        assert text in out

    def test_signal_card_truncation_preserves_prefix(self) -> None:
        """Kalau reasoning panjang, prefix tetap muncul utuh."""
        long_reason = "A" * 500
        sig = _make_signal(reasoning=[long_reason])
        out = format_signal_card(sig)
        # prefix 200 char pertama harus ada verbatim
        assert long_reason[:200] in out
        # ellipsis harus ada
        assert "..." in out

    def test_signal_card_none(self) -> None:
        out = format_signal_card(None)
        assert "No signal" in out

    def test_signal_card_skipped(self) -> None:
        sig = _make_signal(status="SKIPPED")
        out = format_signal_card(sig)
        assert "SKIPPED" in out
        assert "WAIT" in out

    def test_signal_card_invalid(self) -> None:
        sig = _make_signal(status="INVALID")
        out = format_signal_card(sig)
        assert "INVALID" in out

    def test_signal_card_multiple_reasoning_items(self) -> None:
        sig = _make_signal(reasoning=["Reason A", "Reason B", "Reason C"])
        out = format_signal_card(sig)
        assert "Reason A" in out
        assert "Reason B" in out
        assert "Reason C" in out

    def test_signal_card_reasoning_markdown_safe_underscore(self) -> None:
        """Reasoning dengan underscore harus aman untuk Markdown V1."""
        sig = _make_signal(reasoning=["RSI_14 oversold"])
        out = format_signal_card(sig)
        assert "_" not in out
        assert "RSI" in out
        assert "oversold" in out

    def test_signal_card_reasoning_markdown_safe_asterisk(self) -> None:
        sig = _make_signal(reasoning=["RSI_14 oversold *and* price < EMA_50"])
        out = format_signal_card(sig)
        # Header card pakai *intentional* untuk bold Markdown.
        # Cek hanya bagian reasoning yang harus neutral dari * dan _.
        assert "Reasoning:" in out
        reasoning_part = out.split("Reasoning:", 1)[1]
        assert "_" not in reasoning_part
        assert "*" not in reasoning_part
        # Fragmen kata tetap ada (setelah neutralisasi)
        assert "and" in reasoning_part
        assert "RSI" in reasoning_part

    def test_signal_card_reasoning_markdown_safe_backtick(self) -> None:
        sig = _make_signal(reasoning=["Price near `support` zone"])
        out = format_signal_card(sig)
        assert "`" not in out
        assert "support" in out

    def test_signal_card_reasoning_markdown_safe_bracket(self) -> None:
        sig = _make_signal(reasoning=["Level [S1] retest"])
        out = format_signal_card(sig)
        assert "[" not in out
        assert "]" not in out
        assert "S1" in out

    def test_signal_card_symbol_markdown_safe(self) -> None:
        """Symbol dengan underscore juga di-escape."""
        sig = _make_signal(symbol="BTC_USD")
        out = format_signal_card(sig)
        assert "BTC" in out


# ---------- format_portfolio_card ----------


class TestPortfolioCard:
    def test_portfolio_card_contains_core_fields(self) -> None:
        out = format_portfolio_card(_make_state())
        assert "Portfolio" in out
        assert "Equity" in out
        assert "Realized PnL" in out
        assert "Unrealized PnL" in out
        assert "Total PnL" in out
        assert "Open Positions" in out
        assert "Closed Positions" in out
        assert "Drawdown" in out

    def test_portfolio_card_negative_pnl(self) -> None:
        state = _make_state(
            equity=9800.0, realized=-200.0, total_pnl=-200.0
        )
        out = format_portfolio_card(state)
        assert "-200.00" in out

    def test_portfolio_card_zero_pnl(self) -> None:
        state = _make_state(
            equity=10000.0, realized=0.0, total_pnl=0.0
        )
        out = format_portfolio_card(state)
        assert "0.00" in out

    def test_portfolio_card_none(self) -> None:
        out = format_portfolio_card(None)
        assert "No portfolio" in out


# ---------- format_positions_card ----------


class TestPositionsCard:
    def test_positions_card_contains_core_fields(self) -> None:
        pos = _make_position(symbol="BTC", side=Side.LONG)
        out = format_positions_card([pos])
        assert "BTC" in out
        assert "LONG" in out
        assert "Entry" in out
        assert "SL" in out
        assert "TP" in out
        assert "Size" in out
        assert "OPEN" in out

    def test_positions_card_empty(self) -> None:
        out = format_positions_card([])
        assert "Belum ada posisi" in out

    def test_positions_card_multiple_positions(self) -> None:
        p1 = _make_position(symbol="BTC")
        p2 = _make_position(symbol="ETH")
        out = format_positions_card([p1, p2])
        assert "BTC" in out
        assert "ETH" in out

    def test_positions_card_long_vs_short(self) -> None:
        long_pos = _make_position(symbol="BTC", side=Side.LONG)
        short_pos = _make_position(symbol="ETH", side=Side.SHORT)
        out_long = format_positions_card([long_pos])
        out_short = format_positions_card([short_pos])
        assert "LONG" in out_long
        assert "SHORT" in out_short
        # Emoji berbeda
        assert "🟢" in out_long
        assert "🔴" in out_short

    def test_positions_card_no_price_or_pnl_assertion(self) -> None:
        """Sanity: card tidak boleh mengklaim current price / PnL."""
        pos = _make_position()
        out = format_positions_card([pos])
        # Field tidak boleh ada (bukan assertion ketat, hanya guard)
        assert "Current Price" not in out
        assert "Unrealized PnL" not in out
        assert "Progress" not in out


# ---------- format_history_card ----------


class TestHistoryCard:
    def test_history_card_contains_core_fields(self) -> None:
        pos = _make_position(
            status=PositionStatus.CLOSED, duration_minutes=120
        )
        out = format_history_card([pos])
        assert "BTC" in out
        assert "Entry" in out
        assert "Exit" in out
        assert "PnL" in out
        assert "Duration" in out
        assert "Reason" in out

    def test_history_card_duration(self) -> None:
        pos = _make_position(
            status=PositionStatus.CLOSED, duration_minutes=120
        )
        out = format_history_card([pos])
        assert "2h 0m" in out

    def test_history_card_close_reason_is_markdown_safe(self) -> None:
        pos = _make_position(status=PositionStatus.CLOSED)
        pos = pos.model_copy(
            update={"close_reason": PositionCloseReason.STOP_LOSS}
        )
        out = format_history_card([pos])
        assert "STOP LOSS" in out
        assert "_" not in out

    def test_history_card_empty(self) -> None:
        out = format_history_card([])
        assert "Belum ada closed trade" in out

    def test_history_card_limit(self) -> None:
        positions = [
            _make_position(
                symbol=f"SYM{i}", status=PositionStatus.CLOSED
            )
            for i in range(15)
        ]
        out = format_history_card(positions, limit=5)
        # Header hitungan pakai subset
        assert "(5)" in out
        # SYM5..SYM14 tidak boleh masuk (di luar limit)
        assert "SYM10" not in out


# ---------- format_trackrecord_card ----------


class TestTrackRecordCard:
    def test_trackrecord_card_contains_metrics(self) -> None:
        summary = _make_trackrecord()
        out = format_trackrecord_card(summary)
        assert "Win rate" in out
        assert "Wins" in out
        assert "Losses" in out
        assert "Total PnL" in out
        assert "Average PnL" in out

    def test_trackrecord_card_total_and_average_pnl(self) -> None:
        summary = _make_trackrecord(
            closed_count=4, wins=3, losses=1, total_pnl=200.0
        )
        out = format_trackrecord_card(summary)
        assert "200.00" in out
        assert "50.00" in out  # average = 200 / 4

    def test_trackrecord_card_zero_closed(self) -> None:
        summary = _make_trackrecord(
            closed_count=0, wins=0, losses=0, total_pnl=0.0
        )
        out = format_trackrecord_card(summary)
        # Tidak boleh crash division by zero
        assert "0" in out
        assert "Average PnL" in out

    def test_trackrecord_card_average_pnl(self) -> None:
        summary = _make_trackrecord(
            closed_count=5, wins=3, losses=2, total_pnl=100.0
        )
        out = format_trackrecord_card(summary)
        # Average = 100 / 5 = 20
        assert "20.00" in out

    def test_trackrecord_card_no_disclaimer(self) -> None:
        """Tidak menambahkan disclaimer teknis baru."""
        summary = _make_trackrecord()
        out = format_trackrecord_card(summary)
        assert "EARLY_TRACK_RECORD" not in out

    def test_trackrecord_card_none(self) -> None:
        out = format_trackrecord_card(None)
        assert "Track Record" in out
