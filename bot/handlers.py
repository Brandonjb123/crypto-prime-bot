# bot/handlers.py
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
from services.coingecko import get_price
from utils.formatter import format_price
from services.llm import ask_llm
from prompts.system import SYSTEM_PROMPT
from prompts.templates import build_analysis_prompt
from services.news import get_news

SYMBOL_TO_COINGECKO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "SOL": "solana",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "POL": "polygon-ecosystem-token",
    "TRX": "tron",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "ATOM": "cosmos",
    "LTC": "litecoin",
    "FIL": "filecoin",
    "APT": "aptos",
    "ARB": "arbitrum",
    "OP": "optimism",
    "NEAR": "near",
    "INJ": "injective-protocol",
    "SUI": "sui",
    "PEPE": "pepe",
}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    welcome_message = (
        f"👋 Halo {user_first_name}!\n\n"
        "Aku Crypto Prime Assistant, siap bantu analisis trading crypto kamu.\n\n"
        "Ketik /help untuk lihat semua perintah yang tersedia."
    )
    await update.message.reply_text(welcome_message)


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ Mohon masukkan simbol coin.\n"
            "Contoh: `/price BTC` atau `/price ETH`",
        )
        return

    symbol = context.args[0].upper()
    coin_id = SYMBOL_TO_COINGECKO_ID.get(symbol)

    if not coin_id:
        await update.message.reply_text(
            f"❌ Simbol *{symbol}* tidak dikenali.\n"
            "Coba simbol seperti: BTC, ETH, SOL, DOGE, dll.",
        )
        return

    try:
        data = await get_price(coin_id)
        message = format_price(data)
        await update.message.reply_text(message, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text("😔 Gagal mengambil data harga. Coba lagi nanti.")
        logger.error(f"Error /price: {e}")


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "⚠️ Format: `/analyze <PAIR> <TIMEFRAME> <KONDISI_MARKET>`\n\n"
            "Contoh:\n"
            "`/analyze BTC 4H bullish, dekat resistance 64k`\n"
            "`/analyze ETH 1D bearish, turun setelah news SEC`",
        )
        return

    pair = context.args[0].upper()
    timeframe = context.args[1]
    market_condition = " ".join(context.args[2:])

    coin_id = SYMBOL_TO_COINGECKO_ID.get(pair)
    if not coin_id:
        await update.message.reply_text(
            f"❌ Pair *{pair}* tidak dikenali. Gunakan simbol seperti BTC, ETH, SOL.",
        )
        return

    await update.message.reply_text("🔍 Menganalisis setup trade... Mohon tunggu.")

    try:
        price_data = await get_price(coin_id)
        prompt = build_analysis_prompt(pair, timeframe, market_condition, price_data)
        analysis = await ask_llm(SYSTEM_PROMPT, prompt)
        await update.message.reply_text(analysis)
    except Exception as e:
        await update.message.reply_text("😔 Gagal melakukan analisis. Coba lagi nanti.")
        logger.error(f"Error /analyze: {e}")


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ Mohon masukkan pair.\nContoh: `/news BTC` atau `/news ETH`",
        )
        return

    pair = context.args[0].upper()

    await update.message.reply_text(f"📰 Mencari berita terkini untuk *{pair}*...")

    try:
        articles = await get_news(pair)

        if not articles:
            await update.message.reply_text(
                f"😔 Tidak ada berita terkini untuk *{pair}*."
            )
            return

        summary = f"📰 *Berita Terkini — {pair}*\n\n"
        for i, article in enumerate(articles, 1):
            title = article.get("title", "No title")
            source = article.get("source", "Unknown")
            summary += f"{i}. *{title}*\n   Sumber: {source}\n\n"

        await update.message.reply_text(summary, parse_mode="Markdown")

        articles_text = "\n".join([
            f"- {a.get('title', '')} ({a.get('source', '')})"
            for a in articles
        ])
        sentiment_prompt = (
            f"Analisis sentimen berita berikut untuk {pair}. "
            f"Klasifikasikan sebagai Bullish 🟢, Bearish 🔴, atau Neutral ⚪, "
            f"dan beri penjelasan singkat (2-3 kalimat):\n\n{articles_text}"
        )
        sentiment = await ask_llm(SYSTEM_PROMPT, sentiment_prompt)
        await update.message.reply_text(sentiment)

    except Exception as e:
        await update.message.reply_text("😔 Gagal mengambil berita. Coba lagi nanti.")
        logger.error(f"Error /news: {e}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 *Crypto Prime Bot — AI Trading Assistant*

Berikut perintah yang tersedia:

/start — Sapaan dan perkenalan
/price <SYMBOL> — Cek harga real-time
  Contoh: `/price BTC`
/analyze <PAIR> <TF> <KONDISI> — Analisis setup trade
  Contoh: `/analyze ETH 1D bearish, dekat support`
/news <PAIR> — Berita terkini & sentimen
  Contoh: `/news BTC`
/help — Tampilkan bantuan ini

⚠️ *Disclaimer:* Bot ini hanya alat bantu analisis, bukan saran keuangan. Selalu lakukan riset sendiri.
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")