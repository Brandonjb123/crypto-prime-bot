from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from loguru import logger
from config import TELEGRAM_BOT_TOKEN
from db.database import init_db
from bot.handlers import (
    start_command, price_command, analyze_command,
    news_command, help_command, usage_command,
    mysignals_command, paperstats_command, setplan_command, 
    upgrade_command, handle_callback, userinfo_command,
)

logger.add("bot.log", rotation="1 day", retention="7 days", level="DEBUG")
logger.info("Starting bot...")

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
    logger.info("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()