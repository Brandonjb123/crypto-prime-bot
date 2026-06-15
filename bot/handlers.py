# bot/handlers.py
import json
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
from services.coingecko import get_price
from utils.formatter import format_price
from services.llm import ask_llm
from prompts.system import SYSTEM_PROMPT
from prompts.templates import build_analysis_prompt
from services.news import get_news
from db.database import init_db
from db.models import register_user
from utils.rate_limiter import check_and_increment, get_remaining
from services.portfolio import add_position, get_positions, remove_position, calculate_pnl
 

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
    user = update.effective_user
    chat_id = update.effective_chat.id

    init_db()
    is_new = register_user(chat_id, user.username, user.first_name)

    if is_new:
        welcome_message = (
            f"👋 Halo {user.first_name}!\n\n"
            "Selamat datang di Crypto Prime Assistant! 🎉\n"
            "Aku siap bantu analisis trading crypto kamu.\n\n"
            "Ketik /help untuk lihat semua perintah yang tersedia."
        )
    else:
        welcome_message = (
            f"👋 Halo lagi {user.first_name}!\n\n"
            "Senang bertemu kamu lagi. Ada yang bisa aku bantu hari ini?\n\n"
            "Ketik /help untuk lihat semua perintah."
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
    # Rate limiting – cek sebelum validasi input
    if not check_and_increment(update.effective_chat.id, "analyze"):
        await update.message.reply_text(
            "⚠️ Kuota harian `/analyze` kamu sudah habis.\n"
            "Silakan coba lagi besok atau gunakan `/usage` untuk cek sisa kuota."
        )
        return

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
    # Rate limiting – cek sebelum validasi input
    if not check_and_increment(update.effective_chat.id, "news"):
        await update.message.reply_text(
            "⚠️ Kuota harian `/news` kamu sudah habis.\n"
            "Silakan coba lagi besok atau gunakan `/usage` untuk cek sisa kuota."
        )
        return

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


async def addposition_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("DEBUG: /addposition dipanggil")
    """Handler /addposition <pair> <long/short> <entry_price> <amount>"""
    if not context.args or len(context.args) < 4:
        await update.message.reply_text(
            "⚠️ Format: `/addposition <PAIR> <long/short> <ENTRY_PRICE> <AMOUNT>`\n\n"
            "Contoh:\n"
            "`/addposition BTC long 65000 0.01`\n"
            "`/addposition ETH short 3200 0.5`"
        )
        return

    pair = context.args[0].upper()
    side = context.args[1].lower()

    if side not in ("long", "short"):
        await update.message.reply_text("❌ Side harus `long` atau `short`.")
        return

    try:
        entry_price = float(context.args[2])
        amount = float(context.args[3])
    except ValueError:
        await update.message.reply_text("❌ Entry price dan amount harus angka.")
        return

    chat_id = update.effective_chat.id
    position_id = add_position(chat_id, pair, side, entry_price, amount)

    reply_msg = (
        f"✅ Posisi berhasil dicatat!\n\n"
        f"🔹 ID: {position_id}\n"
        f"🔹 Pair: {pair}\n"
        f"🔹 Side: {side.upper()}\n"
        f"🔹 Entry: ${entry_price:,.2f}\n"
        f"🔹 Amount: {amount}\n\n"
        f"Gunakan /myportfolio untuk lihat semua posisi."
    )
    await update.message.reply_text(reply_msg)  # tanpa parse_mode


async def removeposition_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /removeposition <id>"""
    if not context.args:
        await update.message.reply_text("⚠️ Format: `/removeposition <ID>`")
        return

    try:
        position_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID harus angka.")
        return

    chat_id = update.effective_chat.id
    deleted = remove_position(chat_id, position_id)

    if deleted:
        await update.message.reply_text(f"✅ Posisi #{position_id} dihapus.")
    else:
        await update.message.reply_text(f"❌ Posisi #{position_id} tidak ditemukan.")


async def myportfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /myportfolio — tampilkan posisi tanpa P&L dulu"""
    chat_id = update.effective_chat.id
    positions = get_positions(chat_id)

    if not positions:
        await update.message.reply_text("📭 Kamu belum punya posisi aktif.")
        return

    message = "📋 *Portfolio Kamu*\n\n"
    for pos in positions:
        message += (
            f"#{pos['id']} *{pos['pair']}* {pos['side'].upper()}\n"
            f"   Entry: ${pos['entry_price']:,.2f}\n"
            f"   Amount: {pos['amount']}\n\n"
        )
    await update.message.reply_text(message, parse_mode="Markdown")


async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /usage — cek sisa kuota harian."""
    chat_id = update.effective_chat.id
    remaining = get_remaining(chat_id)

    message = (
        "📊 *Kuota Harian Kamu*\n\n"
        f"🔍 /analyze : {remaining['analyze_remaining']}x tersisa\n"
        f"📰 /news    : {remaining['news_remaining']}x tersisa\n\n"
        "Kuota di-reset setiap hari pukul 00:00 UTC."
    )
    await update.message.reply_text(message, parse_mode="Markdown")


async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /backup — export semua posisi ke JSON"""
    chat_id = update.effective_chat.id
    positions = get_positions(chat_id)
    
    if not positions:
        await update.message.reply_text("📭 Tidak ada posisi untuk di-backup.")
        return
    
    # Konversi ke format yang bisa di-restore
    export_data = []
    for p in positions:
        export_data.append({
            "pair": p["pair"],
            "side": p["side"],
            "entry_price": p["entry_price"],
            "amount": p["amount"]
        })
    
    json_str = json.dumps(export_data)
    await update.message.reply_text(
        f"📦 *Backup Posisi*\n\n"
        f"Salin teks berikut untuk `/restore` nanti:\n\n"
        f"`{json_str}`",
        parse_mode="Markdown"
    )

async def restore_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /restore <json> — import posisi dari backup"""
    if not context.args:
        await update.message.reply_text("⚠️ Format: `/restore <JSON>`\nGunakan hasil dari `/backup`.")
        return
    
    json_str = " ".join(context.args)
    try:
        data = json.loads(json_str)
    except:
        await update.message.reply_text("❌ Format JSON tidak valid.")
        return
    
    chat_id = update.effective_chat.id
    count = 0
    for item in data:
        add_position(chat_id, item["pair"], item["side"], item["entry_price"], item["amount"])
        count += 1
    
    await update.message.reply_text(f"✅ {count} posisi berhasil di-restore.\nGunakan `/myportfolio` untuk lihat.")

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /backup — export semua posisi ke JSON"""
    chat_id = update.effective_chat.id
    positions = get_positions(chat_id)
    
    if not positions:
        await update.message.reply_text("📭 Tidak ada posisi untuk di-backup.")
        return
    
    export_data = []
    for p in positions:
        export_data.append({
            "pair": p["pair"],
            "side": p["side"],
            "entry_price": p["entry_price"],
            "amount": p["amount"]
        })
    
    json_str = json.dumps(export_data)
    await update.message.reply_text(
        f"📦 *Backup Posisi*\n\n"
        f"Salin teks berikut untuk `/restore` nanti:\n\n"
        f"`{json_str}`",
        parse_mode="Markdown"
    )

async def restore_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /restore <json> — import posisi dari backup"""
    if not context.args:
        await update.message.reply_text("⚠️ Format: `/restore <JSON>`\nGunakan hasil dari `/backup`.")
        return
    
    json_str = " ".join(context.args)
    try:
        data = json.loads(json_str)
    except:
        await update.message.reply_text("❌ Format JSON tidak valid.")
        return
    
    chat_id = update.effective_chat.id
    count = 0
    for item in data:
        add_position(chat_id, item["pair"], item["side"], item["entry_price"], item["amount"])
        count += 1
    
    await update.message.reply_text(f"✅ {count} posisi berhasil di-restore.\nGunakan `/myportfolio` untuk lihat.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 *Crypto Prime Bot — AI Trading Assistant*

📊 *Market Data*
/price <SYMBOL> — Cek harga real-time
  Contoh: `/price BTC`

🔍 *Analisis AI*
/analyze <PAIR> <TF> <KONDISI> — Analisis setup trade
  Contoh: `/analyze ETH 1D bearish, dekat support`
/news <PAIR> — Berita terkini & sentimen
  Contoh: `/news BTC`

💼 *Portfolio*
/addposition <PAIR> <long/short> <ENTRY> <AMOUNT> — Catat posisi
  Contoh: `/addposition BTC long 65000 0.01`
/myportfolio — Lihat semua posisi & P&L real-time
/removeposition <ID> — Hapus posisi

💾 *Backup & Restore*
/backup — Export semua posisi ke teks
/restore <JSON> — Import posisi dari backup

📋 *Lainnya*
/usage — Cek sisa kuota harian
/help — Tampilkan bantuan ini 


⚠️ *Disclaimer:* Bot ini hanya alat bantu analisis, bukan saran keuangan. Selalu lakukan riset sendiri.
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")