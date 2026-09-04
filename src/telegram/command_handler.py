"""Command Handlers — menampilkan data dari context."""

from datetime import UTC, datetime

from src.commercial.payment_gateway import PaymentGateway, PaymentNotConfiguredError
from src.commercial.subscription_service import SubscriptionService
from src.commercial.telegram_disclaimer import (
    EARLY_TRACK_RECORD,
    PRIVACY_POLICY,
    RISK_DISCLAIMER,
    TERMS_OF_SERVICE,
)
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


def _sync_price(portfolio_manager, pipeline_runner) -> None:
    """Update harga terbaru dari pipeline ke price_provider portfolio."""
    if not portfolio_manager or not pipeline_runner:
        return

    price_provider = getattr(portfolio_manager, "price_provider", None)
    market_snapshot = getattr(pipeline_runner, "last_market_snapshot", None)

    if price_provider and market_snapshot:
        try:
            price_provider.update_price(market_snapshot.symbol, market_snapshot.current_price)
        except Exception:
            pass


def start_handler(message: TelegramMessage | None, context: dict | None = None) -> TelegramResponse:
    ctx = _ctx(context)

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
    pipeline_runner = ctx.get("pipeline_runner")
    if pipeline_runner is not None:
        market_snapshot = getattr(pipeline_runner, "last_market_snapshot", None)
    else:
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
    pipeline_runner = ctx.get("pipeline_runner")

    # Pastikan harga terbaru masuk ke price provider sebelum menghitung posisi
    _sync_price(portfolio_manager, pipeline_runner)

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
    pipeline_runner = ctx.get("pipeline_runner")

    # Pastikan harga terbaru masuk sebelum mengambil state portfolio
    _sync_price(portfolio_manager, pipeline_runner)

    snapshot = None
    if portfolio_manager:
        get_snapshot = getattr(portfolio_manager, "get_state", None)
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

async def subscribe_handler(msg, ctx=None):
    chat_id = int(msg.chat_id)
    svc = SubscriptionService()
    sub = await svc.get(chat_id)

    if sub.status.value == "active":
        return TelegramResponse(
            "✅ Kamu sudah menjadi subscriber aktif.",
            response_type=TelegramResponseType.SUCCESS,
        )

    text = (
        "🚀 *Crypto Prime Early Access*\n\n"
        "Fitur:\n"
        "• Sinyal AI multi-factor\n"
        "• Portfolio paper trading\n"
        "• Early track record\n\n"
        f"{EARLY_TRACK_RECORD}\n\n"
        "💰 Harga: Rp 250.000/bulan\n\n"
        "Ketik /checkout untuk mulai pembayaran."
    )
    return TelegramResponse(text, response_type=TelegramResponseType.SUCCESS)


async def checkout_handler(msg, ctx=None):
    chat_id = int(msg.chat_id)
    gateway = PaymentGateway(None)

    try:
        checkout = await gateway.create_checkout(chat_id, "early_access", 250_000)
        url = checkout.get("url", "Payment link belum tersedia")
        text = (
            "🔗 Lanjutkan pembayaran di sini:\n\n"
            f"{url}\n\n"
            "Setelah selesai, hubungi admin untuk aktivasi."
        )
    except PaymentNotConfiguredError:
        text = (
            "⚠️ Payment provider belum dikonfigurasi.\n"
            "Kamu belum bisa menyelesaikan pembayaran.\n"
            "Tim admin akan mengaktifkan akses manual."
        )

    return TelegramResponse(text, response_type=TelegramResponseType.SUCCESS)


async def terms_handler(msg, ctx=None):
    return TelegramResponse(TERMS_OF_SERVICE, response_type=TelegramResponseType.SUCCESS)


async def privacy_handler(msg, ctx=None):
    return TelegramResponse(PRIVACY_POLICY, response_type=TelegramResponseType.SUCCESS)


async def risk_handler(msg, ctx=None):
    return TelegramResponse(RISK_DISCLAIMER, response_type=TelegramResponseType.SUCCESS)


async def subscription_status_handler(msg, ctx=None):
    chat_id = int(msg.chat_id)
    svc = SubscriptionService()
    sub = await svc.check_and_update(chat_id)

    status_emoji = {
        "free": "🆓",
        "active": "✅",
        "expired": "⏳",
        "cancelled": "❌"
    }.get(sub.status.value, "⚪")

    text = (
        f"{status_emoji} *Status Langganan*\n\n"
        f"Plan: Early Access\n"
        f"Status: {sub.status.value.upper()}\n"
    )
    if sub.expiry_date:
        text += f"Berlaku sampai: {sub.expiry_date.strftime('%d %b %Y')}\n"

    return TelegramResponse(text, response_type=TelegramResponseType.SUCCESS)