"""Formatter untuk pesan Telegram."""

from src.core.models.portfolio import PortfolioSnapshot
from src.core.models.position import Position


def format_positions(positions: list[Position]) -> str:
    if not positions:
        return "📭 No open positions."
    lines = ["📊 *Open Positions*", ""]
    for p in positions:
        lines.append(
            f"• {p.symbol} {p.side.value} | Size: {p.position_size} | Entry: {p.entry_price:.2f}"
        )
    return "\n".join(lines)


def format_portfolio(snapshot: PortfolioSnapshot | None) -> str:
    if not snapshot:
        return "📭 No portfolio snapshot available."
    return (
        f"💰 *Portfolio*\n"
        f"Equity: {snapshot.equity:.2f} USDT\n"
        f"Unrealized PnL: {snapshot.unrealized_pnl:.2f}\n"
        f"Exposure: {snapshot.gross_exposure:.2f}"
    )


def format_status(orchestrator_status: str, pipeline_status: str) -> str:
    return f"🤖 *Bot Status*\nStatus: {orchestrator_status}\nPipeline: {pipeline_status}"


def format_help() -> str:
    return (
        "📋 *Available Commands*\n"
        "/status — Bot status\n"
        "/positions — Open positions\n"
        "/portfolio — Portfolio snapshot\n"
        "/help — This help"
    )
