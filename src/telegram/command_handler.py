"""Command Handlers — context opsional."""

from datetime import UTC, datetime

from src.core.models.telegram import TelegramMessage, TelegramResponse
from src.core.types.enums import TelegramResponseType
from src.telegram.formatter import format_help, format_portfolio, format_positions, format_status


def status_handler(message: TelegramMessage, context: dict | None = None) -> TelegramResponse:
    ctx = context or {}
    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=format_status(
            ctx.get("orchestrator_status", "UNKNOWN"), ctx.get("pipeline_status", "IDLE")
        ),
        timestamp=datetime.now(UTC),
    )


def positions_handler(message: TelegramMessage, context: dict | None = None) -> TelegramResponse:
    ctx = context or {}
    positions = ctx.get("positions", [])
    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=format_positions(positions),
        timestamp=datetime.now(UTC),
    )


def portfolio_handler(message: TelegramMessage, context: dict | None = None) -> TelegramResponse:
    ctx = context or {}
    snapshot = ctx.get("portfolio_snapshot")
    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=format_portfolio(snapshot),
        timestamp=datetime.now(UTC),
    )


def help_handler(message: TelegramMessage, context: dict | None = None) -> TelegramResponse:
    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=format_help(),
        timestamp=datetime.now(UTC),
    )


def last_signal_handler(message: TelegramMessage, context: dict | None = None) -> TelegramResponse:
    ctx = context or {}
    signal = ctx.get("last_signal", "No signal data")
    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=f"📡 Last Signal: {signal}",
        timestamp=datetime.now(UTC),
    )
