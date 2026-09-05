"""Command handlers untuk Telegram."""

from datetime import UTC, datetime

from src.commercial.payment_gateway import PaymentGateway, PaymentNotConfiguredError
from src.commercial.subscription_service import SubscriptionService
from src.commercial.telegram_disclaimer import (
    EARLY_TRACK_RECORD,
    PRIVACY_POLICY,
    RISK_DISCLAIMER,
    TERMS_OF_SERVICE,
)
from src.core.models.telegram import TelegramResponse
from src.core.types.enums import TelegramResponseType
from src.telegram.formatter import (
    format_portfolio,
    format_positions,
    format_signal,
    format_status,
)


def _text_response(text: str) -> TelegramResponse:
    return TelegramResponse(
        text=text,
        response_type=TelegramResponseType.TEXT,
        timestamp=datetime.now(UTC),
    )


def start_handler(msg=None, ctx=None):
    text = (
        "👋 *Selamat datang di Crypto Prime*\n\n"
        "AI-powered crypto intelligence & paper trading.\n"
        "Gunakan menu di bawah untuk menjelajah fitur.\n\n"
        f"{EARLY_TRACK_RECORD}\n\n"
        "Pilih salah satu tombol di bawah ini."
    )
    return _text_response(text)


def help_handler(msg=None, ctx=None):
    text = (
        "🤖 *Crypto Prime Bot — Menu Bantuan*\n\n"
        "📊 *Data & Sinyal*\n"
        "/signals — Sinyal terbaru\n"
        "/positions — Posisi aktif\n"
        "/portfolio — Ringkasan portfolio\n"
        "/history — Riwayat trading\n"
        "/trackrecord — Track record paper trading\n\n"
        "⭐ *Early Access*\n"
        "/subscribe — Info langganan\n"
        "/checkout — Mulai pembayaran\n"
        "/status — Status langganan\n\n"
        "📜 *Legal*\n"
        "/terms — Terms of Service\n"
        "/privacy — Privacy Policy\n"
        "/risk — Risk Disclaimer\n\n"
        "ℹ️ Bisa juga pakai menu utama untuk navigasi."
    )
    return _text_response(text)


def last_signal_handler(msg=None, ctx=None):
    signal = ctx.get("signal") if ctx else None
    if signal is None:
        text = "📡 *Sinyal Terkini*\n\nBelum ada sinyal aktif yang tersedia."
    else:
        text = format_signal(signal)
    return _text_response(text)


def signals_handler(msg=None, ctx=None):
    return last_signal_handler(msg, ctx)


def portfolio_handler(msg=None, ctx=None):
    snapshot = ctx.get("portfolio_snapshot") if ctx else None
    text = format_portfolio(snapshot)
    return _text_response(text)


def positions_handler(msg=None, ctx=None):
    positions = ctx.get("positions") if ctx else None
    if positions is None:
        text = "📈 *Posisi Aktif*\n\nBelum ada posisi open."
    else:
        text = format_positions(positions)
    return _text_response(text)


def history_handler(msg=None, ctx=None):
    closed = ctx.get("closed_positions") if ctx else []

    if not closed:
        return _text_response("📜 *Riwayat Trading Paper*\n\nBelum ada closed trade.")

    lines = ["📜 *Riwayat Trading Paper*\n"]
    for p in closed:
        symbol = getattr(p, "symbol", "N/A")
        side = getattr(p, "side", "N/A")
        entry = getattr(p, "entry_price", 0.0)
        exit_price = getattr(p, "last_price", 0.0)
        size = getattr(p, "position_size", 0.0)
        reason = getattr(p, "close_reason", "MANUAL")

        if side == "LONG":
            pnl = (exit_price - entry) * size
        else:
            pnl = (entry - exit_price) * size

        lines.append(
            f"{symbol} {side}\n"
            f"Entry: ${entry:.2f}\n"
            f"Exit: ${exit_price:.2f}\n"
            f"Reason: {reason}\n"
            f"PnL: ${pnl:.2f}\n"
        )
    return _text_response("\n".join(lines))


def trackrecord_handler(msg=None, ctx=None):
    closed = ctx.get("closed_positions") if ctx else []

    total_closed = len(closed)
    wins = 0
    losses = 0
    total_pnl = 0.0

    for p in closed:
        side = getattr(p, "side", "N/A")
        entry = getattr(p, "entry_price", 0.0)
        exit_price = getattr(p, "last_price", 0.0)
        size = getattr(p, "position_size", 0.0)

        if side == "LONG":
            pnl = (exit_price - entry) * size
        else:
            pnl = (entry - exit_price) * size

        total_pnl += pnl
        if pnl > 0:
            wins += 1
        elif pnl < 0:
            losses += 1

    win_rate = (wins / total_closed * 100) if total_closed else 0.0

    text = (
        "📋 *Track Record — Paper Trading*\n\n"
        f"Closed trades: {total_closed}\n"
        f"Wins: {wins}\n"
        f"Losses: {losses}\n"
        f"Win rate: {win_rate:.1f}%\n"
        f"Total PnL: ${total_pnl:.2f}\n\n"
        f"{EARLY_TRACK_RECORD}"
    )
    return _text_response(text)


def status_handler(msg=None, ctx=None):
    health = ctx.get("orchestrator_status") if ctx else "UNKNOWN"
    pipeline = ctx.get("pipeline_status") if ctx else "IDLE"
    text = format_status(health, pipeline)
    return _text_response(text)


def subscribe_handler(msg=None, ctx=None):
    chat_id = int(msg.chat_id) if msg else 0
    svc = SubscriptionService()
    sub = svc.get(chat_id)

    if sub.status.value == "active":
        return _text_response("✅ Kamu sudah menjadi subscriber aktif.")

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
    return _text_response(text)


def checkout_handler(msg=None, ctx=None):
    chat_id = int(msg.chat_id) if msg else 0
    gateway = PaymentGateway(None)

    try:
        checkout = gateway.create_checkout(chat_id, "early_access", 250_000)
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

    return _text_response(text)


def terms_handler(msg=None, ctx=None):
    return _text_response(TERMS_OF_SERVICE)


def privacy_handler(msg=None, ctx=None):
    return _text_response(PRIVACY_POLICY)


def risk_handler(msg=None, ctx=None):
    return _text_response(RISK_DISCLAIMER)


def subscription_status_handler(msg=None, ctx=None):
    chat_id = int(msg.chat_id) if msg else 0
    svc = SubscriptionService()
    sub = svc.check_and_update(chat_id)

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

    return _text_response(text)