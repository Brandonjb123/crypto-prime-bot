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
    signals = await scan_market(limit=100)
    if signals:
        await broadcast_signals(context.bot, signals)


async def check_signal_warnings(context):
    """Job tiap 20 menit — cek signal yang mendekati TP/SL."""
    near_signals = await check_near_target_signals()

    for item in near_signals:
        sig = item["signal"]
        chat_id = sig["chat_id"]
        pair = sig["pair"]
        signal_type = item["type"]
        current_price = item["current_price"]

        if signal_type == "near_tp":
            message = (
                f"🎯 *{pair}* mendekati Target!\n"
                f"Harga sekarang: {current_price}\n"
                f"Target: {sig['target_price']}"
            )
        else:
            message = (
                f"⚠️ *{pair}* mendekati Stop Loss!\n"
                f"Harga sekarang: {current_price}\n"
                f"Stop Loss: {sig['stop_loss']}"
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