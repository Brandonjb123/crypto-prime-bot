import logging
from telegram.ext import ApplicationBuilder, CommandHandler
from loguru import logger
from config import TELEGRAM_BOT_TOKEN
from bot.handlers import (
    start_command,
    price_command,
    analyze_command,
    news_command,
    help_command,
)

# Setup loguru ke file dan console
logger.add("bot.log", rotation="1 day", retention="7 days", level="DEBUG")
logger.info("Starting bot...")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("help", help_command))
    logger.info("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()