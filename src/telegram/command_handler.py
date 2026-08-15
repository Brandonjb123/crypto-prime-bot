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

    # Ambil dari objek runtime jika tersedia
    pipeline_runner = ctx.get("pipeline_runner")
    health_monitor = ctx.get("health_monitor")

    if pipeline_runner is not None:
        pipeline_status = getattr(pipeline_runner, "last_pipeline_status", "IDLE")
    else:
        pipeline_status = ctx.get("pipeline_status", "IDLE")

    if health_monitor is not None:
        health = health_monitor.get_health()
        health_status = health.status.value if hasattr(health.status, "value") else str(health.status)
    else:
        health_status = ctx.get("orchestrator_status") or ctx.get("health_status", "UNKNOWN")

    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=format_status(health_status, pipeline_status),
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
    pipeline_runner = ctx.get("pipeline_runner")
    if pipeline_runner is not None:
        signal = getattr(pipeline_runner, "last_signal", None)
    else:
        signal = ctx.get("last_signal")
    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=format_signal(signal),
        timestamp=datetime.now(UTC),
    )


def positions_handler(message: TelegramMessage | None, context: dict | None = None) -> TelegramResponse:
    ctx = _ctx(context)
    portfolio_manager = ctx.get("portfolio_state_manager")
    positions = []
    if portfolio_manager:
        get_positions = getattr(portfolio_manager, "get_open_positions", None)
        if get_positions:
            positions = get_positions()
    else:
        positions = ctx.get("positions", [])
    return TelegramResponse(
        response_type=TelegramResponseType.TEXT,
        text=format_positions(positions),
        timestamp=datetime.now(UTC),
    )


def portfolio_handler(message: TelegramMessage | None, context: dict | None = None) -> TelegramResponse:
    ctx = _ctx(context)
    portfolio_manager = ctx.get("portfolio_state_manager")
    snapshot = None
    if portfolio_manager:
        get_snapshot = getattr(portfolio_manager, "get_snapshot", None)
        if get_snapshot:
            snapshot = get_snapshot()
    if snapshot is None:
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