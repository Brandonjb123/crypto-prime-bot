"""Formatter untuk tampilan Telegram."""

from typing import Any

from src.telegram.use_cases import TrackRecordSummary


def format_help() -> str:
    return (
        "🤖 *Crypto Prime Bot*\n"
        "AI Crypto Intelligence & Paper Trading\n\n"
        "📋 *Commands:*\n"
        "/start — Main dashboard\n"
        "/status — System status\n"
        "/positions — Open positions\n"
        "/portfolio — Portfolio snapshot\n"
        "/lastsignal — Latest signal\n"
        "/help — Help menu\n\n"
        "🔒 Live trading: *DISABLED*\n"
        "📝 Mode: *PAPER*"
    )


def format_status(health_status: str, pipeline_status: str) -> str:
    # Jika health_status tidak ada, coba orchestrator_status (dari test lama)
    # Sudah di-handler di command_handler nanti
    return (
        "🤖 *Crypto Prime Bot*\n"
        "AI Crypto Intelligence & Paper Trading\n\n"
        f"🟢 System: ONLINE\n"
        f"📝 Mode: PAPER\n"
        f"📊 Market: BTCUSDT\n"
        f"⏱ Timeframe: 4H\n\n"
        f"⚙️ Pipeline: {pipeline_status or 'IDLE'}\n"
        f"💚 Health: {health_status or 'UNKNOWN'}"
    )


def format_market(market_snapshot: Any) -> str:
    if market_snapshot is None:
        return "⚠️ Market data unavailable"

    return (
        "📊 *Market View*\n\n"
        f"Symbol: {market_snapshot.symbol}\n"
        f"Timeframe: {market_snapshot.timeframe}\n"
        f"Current Price: ${market_snapshot.current_price:,.2f}\n"
        f"Volume 24h: ${market_snapshot.volume_24h:,.0f}\n"
        f"Change 24h: {market_snapshot.change_24h}%\n"
        f"Last Update: {market_snapshot.timestamp:%Y-%m-%d %H:%M:%S UTC}"
    )


def format_signal(signal: Any) -> str:
    if signal is None:
        return "📭 No signal available"

    if hasattr(signal, "status") and signal.status == "SKIPPED":
        return (
            "📈 *Latest Signal*\n\n"
            "🟡 WAIT\n\n"
            "Status: SKIPPED\n"
            "Symbol: " + getattr(signal, "symbol", "N/A") + "\n"
            "Reason: WAIT decision"
        )

    if hasattr(signal, "status") and signal.status == "INVALID":
        return (
            "📈 *Latest Signal*\n\n"
            "⚠️ INVALID SIGNAL\n\n"
            "Status: INVALID\n"
            "Symbol: " + getattr(signal, "symbol", "N/A")
        )

    return (
        "📈 *Latest Signal*\n\n"
        f"🟢 {getattr(signal, 'side', 'N/A')} {getattr(signal, 'symbol', 'N/A')}\n\n"
        f"Entry: ${getattr(signal, 'entry_price', 0.0):,.2f}\n"
        f"SL: ${getattr(signal, 'stop_loss', 0.0):,.2f}\n"
        f"TP: ${getattr(signal, 'take_profit', 0.0):,.2f}\n\n"
        f"Confidence: {getattr(signal, 'confidence', 0)}%\n"
        f"Risk Level: {getattr(signal, 'risk_level', 'N/A')}\n"
        f"Position Size: {getattr(signal, 'position_size', 0.0)}\n\n"
        "📝 PAPER"
    )


def format_positions(positions: list) -> str:
    if not positions:
        return "No open positions."

    lines = ["📋 *Open Positions*\n"]
    for p in positions:
        side = getattr(p, "side", "N/A")
        emoji = "🟢" if side == "LONG" else "🔴"
        lines.append(
            f"{emoji} {getattr(p, 'symbol', 'N/A')} {side}\n"
            f"   Entry: ${getattr(p, 'entry_price', 0.0):,.2f}\n"
            f"   Size: {getattr(p, 'position_size', 0.0)}\n"
            f"   SL: ${getattr(p, 'stop_loss', 0.0):,.2f}\n"
            f"   TP: ${getattr(p, 'take_profit', 0.0):,.2f}\n"
        )
    return "\n".join(lines)


def format_portfolio(snapshot: Any) -> str:
    if snapshot is None:
        return "No portfolio snapshot"

    equity = getattr(snapshot, "equity", 0.0)
    realized = getattr(snapshot, "realized_pnl", 0.0)
    unrealized = getattr(snapshot, "unrealized_pnl", 0.0)
    total_pnl = getattr(snapshot, "total_pnl", 0.0)
    balance = getattr(snapshot, "account_balance", 0.0)
    drawdown = getattr(snapshot, "drawdown", 0.0)
    drawdown_pct = getattr(snapshot, "drawdown_percent", 0.0)
    open_positions = getattr(snapshot, "open_positions", 0)
    closed_positions = getattr(snapshot, "closed_positions", 0)

    return (
        "💼 *Portfolio*\n\n"
        f"Balance: ${balance:.2f}\n"
        f"Equity: ${equity:.2f}\n"
        f"Realized PnL: ${realized:.2f}\n"
        f"Unrealized PnL: ${unrealized:.2f}\n"
        f"Total PnL: ${total_pnl:.2f}\n"
        f"Open Positions: {open_positions}\n"
        f"Closed Positions: {closed_positions}\n"
        f"Drawdown: ${drawdown:.2f} ({drawdown_pct}%)\n"
        "Mode: PAPER"
    )


def format_performance(report: Any) -> str:
    if report is None:
        return "⚠️ Performance data unavailable"

    return (
        "📊 *Performance*\n\n"
        f"Trades: {report.total_trades}\n"
        f"Win Rate: {report.win_rate}%\n"
        f"Net PnL: ${report.net_profit:,.2f}\n"
        f"Profit Factor: {report.profit_factor if report.profit_factor is not None else 'N/A'}\n"
        f"Expectancy: ${report.expectancy:,.2f}\n"
        f"Max Drawdown: {report.max_drawdown_percent}%\n"
        f"Total Fees: ${report.total_fees:,.2f}\n"
        f"Long Win Rate: {report.long_win_rate}%\n"
        f"Short Win Rate: {report.short_win_rate}%"
    )

def format_signals_summary(signals: list) -> str:
    """Format latest signal per symbol — compact list view.

    Setiap entry satu baris ringkas. Dipakai oleh /signals untuk
    menampilkan signal terbaru dari setiap tracked symbol.
    """
    if not signals:
        return "📡 *Sinyal Terkini*\n\nBelum ada sinyal tersedia."

    lines = [f"📡 *Sinyal Terkini — {len(signals)} symbol*\n"]

    for sig in signals:
        symbol = getattr(sig, "symbol", "N/A")
        side = getattr(sig, "side", "N/A")
        status = getattr(sig, "status", "N/A")
        confidence = getattr(sig, "confidence", 0)
        risk_level = getattr(sig, "risk_level", "MEDIUM")

        if status == "ACTIVE":
            emoji = "🟢" if side == "BUY" else "🔴"
            entry = getattr(sig, "entry_price", 0) or 0
            sl = getattr(sig, "stop_loss", 0) or 0
            tp = getattr(sig, "take_profit", 0) or 0
            lines.append(
                f"{emoji} *{symbol}* {side}\n"
                f"   Entry: ${entry:,.2f} | SL: ${sl:,.2f} | TP: ${tp:,.2f}\n"
                f"   Conf: {confidence}% | Risk: {risk_level}\n"
            )
        elif status == "SKIPPED":
            lines.append(f"🟡 *{symbol}* WAIT (SKIPPED)\n")
        else:  # INVALID
            lines.append(f"⚠️ *{symbol}* INVALID\n")

    return "\n".join(lines)

# ---------- Markdown helpers (Phase B) ----------


def _md_safe(value: Any) -> str:
    """Escape underscore untuk Telegram legacy Markdown V1.

    Konvensi sama dengan command_handler._md_safe (tidak diimport untuk
    menghindari circular dependency). STOP_LOSS -> STOP LOSS.
    """
    raw = getattr(value, "value", value)
    return str(raw).replace("_", " ")


def _format_duration(opened_at: Any, closed_at: Any) -> str:
    """Display-only duration formatter.

    Returns "Xh Ym" atau "N/A" kalau timestamp tidak valid/missing.
    """
    if opened_at is None or closed_at is None:
        return "N/A"
    try:
        delta = closed_at - opened_at
    except TypeError:
        return "N/A"
    total_seconds = delta.total_seconds()
    if total_seconds < 0:
        return "N/A"
    total_minutes = int(total_seconds // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"


def _truncate(text: str, max_len: int = 200) -> str:
    """Deterministic truncation. Hanya memotong, tidak mengubah wording."""
    if text is None:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


# ---------- Phase B card formatters ----------


def format_signal_card(signal: Any) -> str:
    """Rich signal card. Reasoning dipertahankan verbatim (hanya truncate)."""
    if signal is None:
        return "📭 No signal available"

    status = getattr(signal, "status", "N/A")
    symbol = getattr(signal, "symbol", "N/A")

    if status == "SKIPPED":
        return (
            "📈 *Signal Card*\n\n"
            "🟡 WAIT\n\n"
            f"Symbol: {symbol}\n"
            f"Status: {status}\n"
            "Reason: WAIT decision"
        )

    if status == "INVALID":
        return (
            "📈 *Signal Card*\n\n"
            "⚠️ INVALID SIGNAL\n\n"
            f"Symbol: {symbol}\n"
            f"Status: {status}"
        )

    side = getattr(signal, "side", "N/A")
    emoji = "🟢" if side == "BUY" else "🔴"
    entry = getattr(signal, "entry_price", 0.0) or 0.0
    sl = getattr(signal, "stop_loss", 0.0) or 0.0
    tp = getattr(signal, "take_profit", 0.0) or 0.0
    confidence = getattr(signal, "confidence", 0)
    risk_level = getattr(signal, "risk_level", "N/A")
    created_at = getattr(signal, "created_at", None)

    ts_str = "N/A"
    if created_at is not None:
        try:
            ts_str = created_at.strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            ts_str = "N/A"

    reasoning = getattr(signal, "reasoning", None) or []
    if isinstance(reasoning, str):
        reasoning = [reasoning]

    reasoning_block = ""
    if reasoning:
        lines = ["", "Reasoning:"]
        for item in reasoning:
            lines.append(f"• {_truncate(str(item), 200)}")
        reasoning_block = "\n".join(lines)

    return (
        "📈 *Signal Card*\n\n"
        f"{emoji} *{symbol}* {side}\n"
        f"Status: {status}\n\n"
        f"Entry: ${entry:,.2f}\n"
        f"SL: ${sl:,.2f}\n"
        f"TP: ${tp:,.2f}\n\n"
        f"Confidence: {confidence}%\n"
        f"Risk Level: {risk_level}\n"
        f"Time: {ts_str}"
        f"{reasoning_block}\n\n"
        "📝 PAPER"
    )


def format_portfolio_card(snapshot: Any) -> str:
    """Portfolio card. Presentation only — tidak hitung ulang apapun."""
    if snapshot is None:
        return "💼 *Portfolio*\n\nNo portfolio snapshot"

    equity = getattr(snapshot, "equity", 0.0)
    realized = getattr(snapshot, "realized_pnl", 0.0)
    unrealized = getattr(snapshot, "unrealized_pnl", 0.0)
    total_pnl = getattr(snapshot, "total_pnl", 0.0)
    open_positions = getattr(snapshot, "open_positions", 0)
    closed_positions = getattr(snapshot, "closed_positions", 0)
    drawdown = getattr(snapshot, "drawdown", 0.0)
    drawdown_pct = getattr(snapshot, "drawdown_percent", 0.0)

    return (
        "💼 *Portfolio*\n\n"
        f"Equity: ${equity:,.2f}\n"
        f"Realized PnL: ${realized:,.2f}\n"
        f"Unrealized PnL: ${unrealized:,.2f}\n"
        f"Total PnL: ${total_pnl:,.2f}\n\n"
        f"Open Positions: {open_positions}\n"
        f"Closed Positions: {closed_positions}\n\n"
        f"Drawdown: ${drawdown:,.2f} ({drawdown_pct}%)\n"
        "Mode: PAPER"
    )


def format_positions_card(positions: list, metrics_map: dict | None = None) -> str:
    """Positions card.

    Backward compatible: `format_positions_card(positions)` tetap menghasilkan
    output Step 3 (tanpa metrics).

    Dengan `metrics_map` (dict: position_id -> metrics dict), tambahkan
    Current / PnL / Progress to TP per position.
    Formatter hanya presentasi — tidak hitung PnL atau progress.
    """
    if not positions:
        return "📊 *Open Positions*\n\nBelum ada posisi open."

    lines = [f"📊 *Open Positions* ({len(positions)})\n"]
    for p in positions:
        symbol = getattr(p, "symbol", "N/A")
        side_raw = getattr(p, "side", "N/A")
        side = getattr(side_raw, "value", side_raw)
        side_str = str(side).upper()
        emoji = "🟢" if side_str == "LONG" else "🔴"
        size = getattr(p, "position_size", 0.0)
        entry = getattr(p, "entry_price", 0.0)
        sl = getattr(p, "stop_loss", 0.0)
        tp = getattr(p, "take_profit", 0.0)
        status_raw = getattr(p, "status", "N/A")
        status = getattr(status_raw, "value", status_raw)

        lines.append(
            f"{emoji} *{symbol}* {side_str}\n"
            f"   Size: {size}\n"
            f"   Entry: ${entry:,.2f}\n"
            f"   SL: ${sl:,.2f}\n"
            f"   TP: ${tp:,.2f}\n"
        )

        if metrics_map is not None:
            pid = getattr(p, "position_id", None)
            m = metrics_map.get(pid) if pid is not None else None
            if m is not None:
                cp = m.get("current_price")
                pnl = m.get("unrealized_pnl")
                prog = m.get("progress_pct")
                cp_str = f"${cp:,.2f}" if cp is not None else "N/A"
                pnl_str = f"${pnl:,.2f}" if pnl is not None else "N/A"
                prog_str = f"{prog:.1f}%" if prog is not None else "N/A"
                lines.append(
                    f"   Current: {cp_str}\n"
                    f"   PnL: {pnl_str}\n"
                    f"   Progress to TP: {prog_str}\n"
                )

        lines.append(f"   Status: {status}\n")

    return "\n".join(lines)


def format_history_card(closed_positions: list, limit: int = 10) -> str:
    """Closed-trade card. Duration = display-only derivation."""
    if not closed_positions:
        return "📜 *Riwayat Trading Paper*\n\nBelum ada closed trade."

    subset = list(closed_positions)[:limit]
    lines = [f"📜 *Riwayat Trading Paper* ({len(subset)})\n"]

    for p in subset:
        symbol = getattr(p, "symbol", "N/A")
        side_raw = getattr(p, "side", "N/A")
        side = getattr(side_raw, "value", side_raw)
        side_str = str(side).upper()
        entry = getattr(p, "entry_price", 0.0)
        exit_price = getattr(p, "last_price", 0.0)
        pnl = getattr(p, "realized_pnl", 0.0)
        reason = _md_safe(getattr(p, "close_reason", "MANUAL"))
        opened = getattr(p, "opened_at", None)
        closed = getattr(p, "closed_at", None)
        duration = _format_duration(opened, closed)

        lines.append(
            f"{symbol} {side_str}\n"
            f"Entry: ${entry:,.2f}\n"
            f"Exit: ${exit_price:,.2f}\n"
            f"PnL: ${pnl:,.2f}\n"
            f"Duration: {duration}\n"
            f"Reason: {reason}\n"
        )
    return "\n".join(lines)


def format_trackrecord_card(summary: TrackRecordSummary) -> str:
    """Track record card. Input: TrackRecordSummary (ephemeral view model)."""
    if summary is None:
        return "📋 *Track Record — Paper Trading*\n\nNo data"

    return (
        "📋 *Track Record — Paper Trading*\n\n"
        f"Closed trades: {summary.closed_count}\n"
        f"Wins: {summary.wins}\n"
        f"Losses: {summary.losses}\n"
        f"Win rate: {summary.win_rate:.1f}%\n"
        f"Total PnL: ${summary.total_pnl:,.2f}\n"
        f"Average PnL: ${summary.average_pnl:,.2f}"
    )