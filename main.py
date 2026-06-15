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
from db.database import init_db
from bot.handlers import (
    start_command, price_command, analyze_command,
    news_command, help_command, usage_command,
    addposition_command, removeposition_command,
    myportfolio_command, backup_command, restore_command,
    mysignals_command,
)

# Setup loguru ke file dan console
logger.add("bot.log", rotation="1 day", retention="7 days", level="DEBUG")
logger.info("Starting bot...")

def main():
    # Inisialisasi database
    init_db()
    logger.info("Database siap")
    
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("usage", usage_command))
    app.add_handler(CommandHandler("addposition", addposition_command))
    app.add_handler(CommandHandler("removeposition", removeposition_command))
    app.add_handler(CommandHandler("myportfolio", myportfolio_command))
    app.add_handler(CommandHandler("backup", backup_command))
    app.add_handler(CommandHandler("restore", restore_command))
    app.add_handler(CommandHandler("mysignals", mysignals_command))
    logger.info("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()