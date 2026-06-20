from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from loguru import logger
from config import TELEGRAM_BOT_TOKEN
from db.database import init_db
from bot.handlers import (
    start_command, price_command, analyze_command,
    news_command, help_command, usage_command,
    mysignals_command, paperstats_command, setplan_command,
    upgrade_command, handle_callback, userinfo_command,
    scan_command, handle_pair_text_input,
)
from services.scanner import scan_market
from services.broadcaster import broadcast_signals
from services.signals import check_near_target_signals, mark_signal_warned

logger.add("bot.log", rotation="1 day", retention="7 days", level="DEBUG")
logger.info("Starting bot...")


async def scheduled_broadcast(context):
    from config import ADMIN_CHAT_ID
    try:
        signals = await scan_market(limit=100)
        if signals:
            await broadcast_signals(context.bot, signals)
        else:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text="ℹ️ Auto-scan selesai, tidak ada SETUP_VALID ditemukan."
            )
    except Exception as e:
        logger.error(f"Scheduled broadcast gagal total: {e}")
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"⚠️ Auto-broadcast error: {str(e)[:200]}"
            )
        except Exception:
            pass


async def check_signal_warnings(context):
    """Job tiap 20 menit — cek signal yang mendekati TP/SL."""
    from utils.formatter import _smart_price, calculate_leverage_pnl

    near_signals = await check_near_target_signals()

    for item in near_signals:
        sig = item["signal"]
        chat_id = sig["chat_id"]
        pair = sig["pair"]
        signal_type = item["type"]
        current_price = item["current_price"]

        entry = sig["entry_price"]
        target = sig["target_price"]
        sl = sig["stop_loss"]
        side = sig["side"]

        if signal_type == "near_tp":
            distance_pct = abs(target - current_price) / current_price * 100
            pnl_10x = calculate_leverage_pnl(entry, target, sl, side)[10]

            message = (
                f"🎯 *{pair}/USDT mendekati Target!*\n\n"
                f"💰 Harga sekarang : {_smart_price(current_price)}\n"
                f"🎯 Target          : {_smart_price(target)}\n"
                f"📏 Jarak           : {distance_pct:.1f}% lagi\n\n"
                f"💡 Estimasi profit @10x: +{pnl_10x['profit']}%\n\n"
                f"Pantau terus di /mysignals"
            )
        else:  # near_sl
            distance_pct = abs(sl - current_price) / current_price * 100
            pnl_10x = calculate_leverage_pnl(entry, target, sl, side)[10]

            message = (
                f"⚠️ *{pair}/USDT mendekati Stop Loss!*\n\n"
                f"💰 Harga sekarang : {_smart_price(current_price)}\n"
                f"🛑 Stop Loss       : {_smart_price(sl)}\n"
                f"📏 Jarak           : {distance_pct:.1f}% lagi\n\n"
                f"💡 Estimasi loss @10x: -{pnl_10x['loss']}%\n\n"
                f"Pantau terus di /mysignals"
            )

        try:
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
            mark_signal_warned(sig["id"])
        except Exception as e:
            logger.error(f"Gagal kirim warning sinyal #{sig['id']}: {e}")


def main():
    init_db()
    logger.info("Database siap")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("usage", usage_command))
    app.add_handler(CommandHandler("mysignals", mysignals_command))
    app.add_handler(CommandHandler("paperstats", paperstats_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(CommandHandler("setplan", setplan_command))
    app.add_handler(CommandHandler("upgrade", upgrade_command))
    app.add_handler(CommandHandler("userinfo", userinfo_command))
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pair_text_input))

    # Auto broadcast tiap 4 jam
    app.job_queue.run_repeating(
        scheduled_broadcast,
        interval=14400,  # 4 jam
        first=60
    )

    # Early warning TP/SL tiap 20 menit
    app.job_queue.run_repeating(
        check_signal_warnings,
        interval=1200,  # 20 menit
        first=120
    )

    logger.info("Bot berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()