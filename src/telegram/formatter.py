"""Formatter untuk tampilan Telegram."""

from typing import Any


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

    return (
        "💼 *Portfolio*\n\n"
        f"Equity: ${snapshot.equity:.2f}\n"
        f"Realized PnL: ${snapshot.realized_pnl:.2f}\n"
        f"Unrealized PnL: ${snapshot.unrealized_pnl:.2f}\n"
        f"Open Positions: {snapshot.open_positions}\n"
        f"Net Exposure: ${snapshot.net_exposure:.2f}\n"
        f"Gross Exposure: ${snapshot.gross_exposure:.2f}\n"
        f"Status: {snapshot.status}"
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