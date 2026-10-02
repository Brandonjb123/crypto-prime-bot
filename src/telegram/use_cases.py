"""Thin read/use-case layer untuk Telegram presentation.

Read-only helpers yang dipakai bersama oleh command handler dan
callback handler. Tidak ada mutation, tidak ada domain logic baru.
Semua data diambil dari `ctx` yang sudah di-populate oleh runtime.
"""

from dataclasses import dataclass

from src.core.models.portfolio_state import PortfolioState
from src.core.models.position import Position
from src.core.models.trading_signal import TradingSignal
from src.core.types.enums import Side
from src.market.pnl_engine import calculate_position_unrealized


@dataclass(frozen=True)
class TrackRecordSummary:
    """Display-only summary. Bukan domain model, bukan source of truth."""

    closed_count: int
    wins: int
    losses: int
    total_pnl: float
    average_pnl: float
    win_rate: float


def read_portfolio(ctx: dict | None) -> PortfolioState | None:
    """Read portfolio snapshot dari ctx. None kalau tidak ada."""
    if not ctx:
        return None
    return ctx.get("portfolio_snapshot")


def read_positions(ctx: dict | None) -> list[Position]:
    """Read open positions dari ctx. Return list baru (bukan referensi ctx)."""
    if not ctx:
        return []
    return list(ctx.get("positions") or [])


def read_history(ctx: dict | None) -> list[Position]:
    """Read closed positions dari ctx. Return list baru (bukan referensi ctx)."""
    if not ctx:
        return []
    return list(ctx.get("closed_positions") or [])


def read_trackrecord(ctx: dict | None) -> TrackRecordSummary:
    """Derived display-only summary dari closed positions.

    Semua nilai (wins, losses, total_pnl, average_pnl, win_rate) dihitung
    on-the-fly. `realized_pnl` per-position tetap source of truth.

    Definisi win/loss mengikuti existing codebase (trackrecord_handler):
    - win  : realized_pnl > 0
    - loss : realized_pnl < 0
    """
    closed = read_history(ctx)

    closed_count = len(closed)
    wins = sum(1 for p in closed if getattr(p, "realized_pnl", 0.0) > 0)
    losses = sum(1 for p in closed if getattr(p, "realized_pnl", 0.0) < 0)
    total_pnl = sum(getattr(p, "realized_pnl", 0.0) for p in closed)

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


def read_latest_signals(
    ctx: dict | None, symbols: list[str]
) -> list[TradingSignal]:
    """Latest signal per requested symbol. Skip symbol yang belum ada signal.

    Preserve urutan `symbols` di output.
    """
    if not ctx:
        return []
    repo = ctx.get("signal_repository")
    if repo is None:
        return []

    signals: list[TradingSignal] = []
    for symbol in symbols:
        sig = repo.latest_by_symbol(symbol)
        if sig is not None:
            signals.append(sig)
    return signals


def read_last_signal(ctx: dict | None) -> TradingSignal | None:
    """Latest global signal (newest by created_at).

    Mempertahankan semantics existing `/lastsignal`:
    `repo.history()` sorted desc by created_at, ambil index [0].
    Return None kalau belum ada signal atau repo tidak tersedia.
    """
    if not ctx:
        return None
    repo = ctx.get("signal_repository")
    if repo is None:
        return None

    history = repo.history()
    if not history:
        return None
    return history[0]


# ---------- Per-position metrics (Step 5) ----------


def _calculate_progress_pct(position, current_price) -> float | None:
    """Progress entry -> TP, clamped 0-100.

    LONG : (current - entry) / (tp - entry) * 100
    SHORT: (entry - current) / (entry - tp) * 100

    Return None jika:
      - current_price None
      - TP None / 0
      - denominator zero (entry == TP)
    """
    if current_price is None:
        return None

    entry = position.entry_price
    tp = position.take_profit
    if tp is None or tp == 0:
        return None

    if position.side == Side.LONG:
        denom = tp - entry
        if denom == 0:
            return None
        raw = (current_price - entry) / denom * 100
    else:  # SHORT
        denom = entry - tp
        if denom == 0:
            return None
        raw = (entry - current_price) / denom * 100

    return max(0.0, min(100.0, raw))


def read_positions_with_metrics(ctx: dict | None) -> list[dict]:
    """Thin projection: setiap open position + metrics.

    Return list of dicts:
      - position        : Position
      - current_price   : float | None
      - unrealized_pnl  : float | None
      - progress_pct    : float | None

    Tidak mutate posisi. Tidak calculate PnL langsung (pakai helper domain).
    """
    positions = read_positions(ctx)
    if not positions:
        return []

    price_provider = ctx.get("price_provider") if ctx else None

    out: list[dict] = []
    for pos in positions:
        if price_provider is None:
            out.append(
                {
                    "position": pos,
                    "current_price": None,
                    "unrealized_pnl": None,
                    "progress_pct": None,
                }
            )
            continue

        current_price = price_provider.get_price(pos.symbol)
        unrealized = calculate_position_unrealized(pos, price_provider)
        progress = _calculate_progress_pct(pos, current_price)

        out.append(
            {
                "position": pos,
                "current_price": current_price,
                "unrealized_pnl": unrealized,
                "progress_pct": progress,
            }
        )
    return out