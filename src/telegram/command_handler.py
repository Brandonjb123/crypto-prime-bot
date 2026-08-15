"""Command Handlers — menampilkan data dari context."""

from datetime import UTC, datetime

from src.core.models.telegram import TelegramMessage, TelegramResponse
from src.core.types.enums import TelegramResponseType
from src.telegram.formatter import (
    format_help,
    format_market,
    format_performance,
    format_portfolio,
    format_positions,
    format_signal,
    format_status,
)


def _ctx(context: dict | None) -> dict:
    return context or {}


def start_handler(message: TelegramMessage | None, context: dict | None = None) -> TelegramResponse:
    ctx = _ctx(context)
    health = ctx.get("health_status") or ctx.get("orchestrator_status", "UNKNOWN")
    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=format_status(health, ctx.get("pipeline_status", "IDLE")),
        timestamp=datetime.now(UTC),
    )


def status_handler(message: TelegramMessage | None, context: dict | None = None) -> TelegramResponse:
    return start_handler(message, context)


def market_handler(message: TelegramMessage | None, context: dict | None = None) -> TelegramResponse:
    ctx = _ctx(context)
    market_snapshot = ctx.get("market_snapshot")
    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=format_market(market_snapshot),
        timestamp=datetime.now(UTC),
    )


def last_signal_handler(message: TelegramMessage | None, context: dict | None = None) -> TelegramResponse:
    ctx = _ctx(context)
    signal = ctx.get("last_signal")
    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=format_signal(signal),
        timestamp=datetime.now(UTC),
    )


def positions_handler(message: TelegramMessage | None, context: dict | None = None) -> TelegramResponse:
    ctx = _ctx(context)
    positions = ctx.get("positions", [])
    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=format_positions(positions),
        timestamp=datetime.now(UTC),
    )


def portfolio_handler(message: TelegramMessage | None, context: dict | None = None) -> TelegramResponse:
    ctx = _ctx(context)
    snapshot = ctx.get("portfolio_snapshot")
    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=format_portfolio(snapshot),
        timestamp=datetime.now(UTC),
    )


def performance_handler(message: TelegramMessage | None, context: dict | None = None) -> TelegramResponse:
    ctx = _ctx(context)
    performance_report = ctx.get("performance_report")
    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=format_performance(performance_report),
        timestamp=datetime.now(UTC),
    )


def help_handler(message: TelegramMessage | None, context: dict | None = None) -> TelegramResponse:
    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=format_help(),
        timestamp=datetime.now(UTC),
    )