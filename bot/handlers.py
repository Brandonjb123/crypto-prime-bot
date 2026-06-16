# bot/handlers.py
import json
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from services.coingecko import get_price
from services.llm import ask_llm
from services.news import get_news
from services.portfolio import add_position, get_positions, remove_position, calculate_pnl
from services.signals import save_signal, get_open_signals, check_and_update_signal, get_signal_stats

from db.database import init_db
from db.models import register_user

from utils.rate_limiter import check_and_increment, get_remaining
from utils.formatter import format_price, format_analyze, format_signals, format_portfolio, format_paperstats
from utils.symbols import SYMBOL_TO_COINGECKO_ID

from prompts.system import SYSTEM_PROMPT
from prompts.templates import build_analysis_prompt

from bot.keyboards import (
    main_menu_keyboard,
    price_keyboard,
    analyze_keyboard,
    signals_keyboard,
    portfolio_keyboard,
    paperstats_keyboard,
    back_to_menu_keyboard,
)


# ==================== START COMMAND ====================
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

    await update.effective_message.reply_text(
        welcome_message,
        reply_markup=main_menu_keyboard()
    )


# ==================== PRICE COMMAND ====================
async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            "⚠️ Mohon masukkan simbol coin.\n"
            "Contoh: `/price BTC` atau `/price ETH`",
            reply_markup=back_to_menu_keyboard()
        )
        return

    symbol = context.args[0].upper()
    coin_id = SYMBOL_TO_COINGECKO_ID.get(symbol)

    if not coin_id:
        await update.effective_message.reply_text(
            f"❌ Simbol *{symbol}* tidak dikenali.\n"
            "Coba simbol seperti: BTC, ETH, SOL, DOGE, dll.",
            reply_markup=back_to_menu_keyboard()
        )
        return

    try:
        data = await get_price(coin_id)
        message = format_price(data)
        await update.effective_message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=price_keyboard(symbol)
        )
    except Exception as e:
        logger.error(f"Error /price: {e}")
        await update.effective_message.reply_text(
            f"😔 Gagal mengambil data harga. ({str(e)})",
            reply_markup=back_to_menu_keyboard()
        )


# ==================== ANALYZE COMMAND ====================
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_and_increment(update.effective_chat.id, "analyze"):
        await update.effective_message.reply_text(
            "⚠️ Kuota harian `/analyze` kamu sudah habis.\n"
            "Silakan coba lagi besok atau gunakan `/usage` untuk cek sisa kuota."
        )
        return

    chat_id = update.effective_chat.id

    if not context.args or len(context.args) < 3:
        await update.effective_message.reply_text(
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
        await update.effective_message.reply_text(
            f"❌ Pair *{pair}* tidak dikenali. Gunakan simbol seperti BTC, ETH, SOL.",
        )
        return

    await update.effective_message.reply_text("🔍 Menganalisis setup trade... Mohon tunggu.")

    try:
        price_data = await get_price(coin_id)
        prompt = build_analysis_prompt(pair, timeframe, market_condition, price_data)
        analysis = await ask_llm(SYSTEM_PROMPT, prompt)

        try:
            data = json.loads(analysis)
            required = ["side", "entry_price", "target_price", "stop_loss", "summary", "risk_notes"]
            if all(k in data for k in required):
                side = data["side"].lower()
                entry = float(data["entry_price"])
                target = float(data["target_price"])
                stop = float(data["stop_loss"])
                summary = data["summary"]
                risk = data["risk_notes"]

                signal_id = save_signal(chat_id, pair, side, entry, target, stop)

                analyze_data = {
                    "pair": pair,
                    "side": side,
                    "entry_price": entry,
                    "target_price": target,
                    "stop_loss": stop,
                    "summary": summary,
                    "risk_notes": risk,
                }
                message = format_analyze(analyze_data)
                await update.effective_message.reply_text(
                    message,
                    parse_mode="Markdown",
                    reply_markup=analyze_keyboard()
                )
                return
            else:
                raise ValueError("JSON tidak lengkap")
        except (json.JSONDecodeError, ValueError, KeyError) as parse_error:
            logger.warning(f"Gagal parse JSON dari LLM: {parse_error}")
            await update.effective_message.reply_text(analysis)

    except Exception as e:
        await update.effective_message.reply_text("😔 Gagal melakukan analisis. Coba lagi nanti.")
        logger.error(f"Error /analyze: {e}")


# ==================== NEWS COMMAND ====================
async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_and_increment(update.effective_chat.id, "news"):
        await update.effective_message.reply_text(
            "⚠️ Kuota harian `/news` kamu sudah habis.\n"
            "Silakan coba lagi besok atau gunakan `/usage` untuk cek sisa kuota."
        )
        return

    if not context.args:
        await update.effective_message.reply_text(
            "⚠️ Mohon masukkan pair.\nContoh: `/news BTC` atau `/news ETH`",
        )
        return

    pair = context.args[0].upper()

    await update.effective_message.reply_text(f"📰 Mencari berita terkini untuk *{pair}*...")

    try:
        articles = await get_news(pair)
        if not articles:
            await update.effective_message.reply_text(
                f"😔 Tidak ada berita terkini untuk *{pair}*.",
                reply_markup=back_to_menu_keyboard()
            )
            return

        summary = f"📰 *Berita Terkini — {pair}*\n\n"
        for i, article in enumerate(articles, 1):
            title = article.get("title", "No title")
            source = article.get("source", "Unknown")
            summary += f"{i}. *{title}*\n   Sumber: {source}\n\n"

        await update.effective_message.reply_text(summary, parse_mode="Markdown")

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
        await update.effective_message.reply_text(sentiment, reply_markup=back_to_menu_keyboard())

    except Exception as e:
        await update.effective_message.reply_text("😔 Gagal mengambil berita. Coba lagi nanti.")
        logger.error(f"Error /news: {e}")


# ==================== ADD POSITION COMMAND ====================
async def addposition_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("DEBUG: /addposition dipanggil")
    if not context.args or len(context.args) < 4:
        await update.effective_message.reply_text(
            "⚠️ Format: `/addposition <PAIR> <long/short> <ENTRY_PRICE> <AMOUNT>`\n\n"
            "Contoh:\n"
            "`/addposition BTC long 65000 0.01`\n"
            "`/addposition ETH short 3200 0.5`",
            reply_markup=back_to_menu_keyboard()
        )
        return

    pair = context.args[0].upper()
    side = context.args[1].lower()
    if side not in ("long", "short"):
        await update.effective_message.reply_text("❌ Side harus `long` atau `short`.")
        return

    try:
        entry_price = float(context.args[2])
        amount = float(context.args[3])
    except ValueError:
        await update.effective_message.reply_text("❌ Entry price dan amount harus angka.")
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
    await update.effective_message.reply_text(reply_msg, reply_markup=back_to_menu_keyboard())


# ==================== REMOVE POSITION COMMAND ====================
async def removeposition_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("⚠️ Format: `/removeposition <ID>`")
        return

    try:
        position_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("❌ ID harus angka.")
        return

    chat_id = update.effective_chat.id
    deleted = remove_position(chat_id, position_id)

    if deleted:
        await update.effective_message.reply_text(
            f"✅ Posisi #{position_id} dihapus.",
            reply_markup=back_to_menu_keyboard()
        )
    else:
        await update.effective_message.reply_text(
            f"❌ Posisi #{position_id} tidak ditemukan.",
            reply_markup=back_to_menu_keyboard()
        )


# ==================== MY PORTFOLIO COMMAND ====================
async def myportfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    positions = get_positions(chat_id)

    if not positions:
        await update.effective_message.reply_text(
            "📭 Kamu belum punya posisi aktif.\n"
            "Gunakan `/addposition` untuk mencatat posisi.",
            reply_markup=portfolio_keyboard()
        )
        return

    await update.effective_message.reply_text("📊 Menghitung P&L...")

    positions_data = []
    for pos in positions:
        pair = pos["pair"]
        side = pos["side"]
        entry = pos["entry_price"]
        amount = pos["amount"]
        pos_id = pos["id"]

        try:
            coin_id = SYMBOL_TO_COINGECKO_ID.get(pair)
            if not coin_id:
                continue
            price_data = await get_price(coin_id)
            current_price = price_data.get("current_price")
            if current_price is None:
                continue
            pnl_pct = calculate_pnl(entry, current_price, side)
            positions_data.append({
                "id": pos_id,
                "pair": pair,
                "side": side,
                "entry_price": entry,
                "current_price": current_price,
                "pnl_pct": pnl_pct,
                "amount": amount,
            })
        except Exception as e:
            logger.error(f"Error /myportfolio untuk posisi {pos_id}: {e}")

    if positions_data:
        message = format_portfolio(positions_data)
        await update.effective_message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=portfolio_keyboard()
        )
    else:
        await update.effective_message.reply_text(
            "⚠️ Gagal mengambil data harga.",
            reply_markup=portfolio_keyboard()
        )


# ==================== MY SIGNALS COMMAND ====================
async def mysignals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    signals = get_open_signals(chat_id)

    if not signals:
        await update.effective_message.reply_text(
            "📭 Kamu belum punya sinyal aktif.\n"
            "Gunakan `/analyze` untuk dapat rekomendasi trading.",
            reply_markup=signals_keyboard()
        )
        return

    await update.effective_message.reply_text("📡 Mengecek status sinyal...")

    now = datetime.utcnow()
    notifications = []
    updated_signals = []

    for sig in signals:
        sig = await check_and_update_signal(sig)
        if sig["status"] != "open":
            emoji_result = "🎯" if sig["status"] == "hit_target" else "🛑"
            notifications.append(
                f"{emoji_result} *Sinyal #{sig['id']} {sig['pair']} {sig['side'].upper()}* "
                f"telah {sig['status'].replace('_', ' ').title()}! "
                f"P&L: {sig.get('result_pct', 0):+.2f}%"
            )
            continue

        try:
            coin_id = SYMBOL_TO_COINGECKO_ID.get(sig["pair"])
            if coin_id:
                price_data = await get_price(coin_id)
                sig["current_price"] = price_data.get("current_price")
            else:
                sig["current_price"] = sig["entry_price"]
        except Exception:
            sig["current_price"] = sig["entry_price"]

        created_at = datetime.fromisoformat(sig["created_at"])
        age = now - created_at
        hours, remainder = divmod(int(age.total_seconds()), 3600)
        minutes = remainder // 60
        sig["age"] = f"{hours}j {minutes}m" if hours > 0 else f"{minutes}m"
        updated_signals.append(sig)

    for notif in notifications:
        await update.effective_message.reply_text(notif, parse_mode="Markdown")

    if updated_signals:
        message = format_signals(updated_signals)
        await update.effective_message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=signals_keyboard()
        )
    else:
        await update.effective_message.reply_text(
            "📭 Semua sinyal sudah closed. Gunakan `/analyze` untuk dapat sinyal baru.",
            reply_markup=signals_keyboard()
        )


# ==================== PAPER STATS COMMAND ====================
async def paperstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    open_signals = get_open_signals(chat_id)
    notifications = []
    for sig in open_signals:
        sig = await check_and_update_signal(sig)
        if sig["status"] != "open":
            emoji_result = "🎯" if sig["status"] == "hit_target" else "🛑"
            notifications.append(
                f"{emoji_result} *Sinyal #{sig['id']} {sig['pair']} {sig['side'].upper()}* "
                f"baru saja closed: {sig.get('result_pct', 0):+.2f}%"
            )

    for notif in notifications:
        await update.effective_message.reply_text(notif, parse_mode="Markdown")

    stats = get_signal_stats(chat_id)

    if stats["total_closed"] == 0 and stats["open_count"] == 0:
        await update.effective_message.reply_text(
            "📭 Belum ada sinyal tercatat.\n"
            "Gunakan `/analyze` untuk dapat rekomendasi trading.",
            reply_markup=paperstats_keyboard()
        )
        return

    message = format_paperstats(stats)
    await update.effective_message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=paperstats_keyboard()
    )


# ==================== USAGE COMMAND ====================
async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    remaining = get_remaining(chat_id)

    message = (
        "📊 *Kuota Harian Kamu*\n\n"
        f"🔍 /analyze : {remaining['analyze_remaining']}x tersisa\n"
        f"📰 /news    : {remaining['news_remaining']}x tersisa\n\n"
        "Kuota di-reset setiap hari pukul 00:00 UTC."
    )
    await update.effective_message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=back_to_menu_keyboard()
    )


# ==================== BACKUP COMMAND ====================
async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    positions = get_positions(chat_id)

    if not positions:
        await update.effective_message.reply_text(
            "📭 Tidak ada posisi untuk di-backup.",
            reply_markup=back_to_menu_keyboard()
        )
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
    await update.effective_message.reply_text(
        f"📦 *Backup Posisi*\n\n"
        f"Salin teks berikut untuk `/restore` nanti:\n\n"
        f"`{json_str}`",
        parse_mode="Markdown"
    )


# ==================== RESTORE COMMAND ====================
async def restore_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            "⚠️ Format: `/restore <JSON>`\nGunakan hasil dari `/backup`.",
            reply_markup=back_to_menu_keyboard()
        )
        return

    json_str = " ".join(context.args)
    try:
        data = json.loads(json_str)
    except Exception:
        await update.effective_message.reply_text("❌ Format JSON tidak valid.")
        return

    chat_id = update.effective_chat.id
    count = 0
    for item in data:
        add_position(chat_id, item["pair"], item["side"], item["entry_price"], item["amount"])
        count += 1

    await update.effective_message.reply_text(
        f"✅ {count} posisi berhasil di-restore.\nGunakan `/myportfolio` untuk lihat.",
        reply_markup=back_to_menu_keyboard()
    )


# ==================== HELP COMMAND ====================
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

📡 *Paper Trading (Fase 3)*
/analyze — Sekarang otomatis menyimpan sinyal
/mysignals — Lihat sinyal yang masih aktif
/paperstats — Statistik performa sinyal (win rate, avg profit)

💼 *Portfolio Manual*
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
    await update.effective_message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=back_to_menu_keyboard()
    )


# ==================== CALLBACK HANDLER ====================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # --- MENU UTAMA ---
    if data == "menu_start":
        await start_command(update, context)
    elif data == "menu_analyze":
        await query.message.reply_text(
            "Silakan gunakan command /analyze \\<PAIR\\> \\<TF\\> \\<KONDISI\\>\n"
            "Contoh: `/analyze BTC 4H bullish`",
            entities=[{"type": "bot_command", "offset": 24, "length": 8}]
        )
    elif data == "menu_price":
        await query.message.reply_text(
            "Silakan gunakan command /price \\<SYMBOL\\>\n"
            "Contoh: `/price BTC`",
            entities=[{"type": "bot_command", "offset": 24, "length": 6}]
        )
    elif data == "menu_news":
        await query.message.reply_text(
            "Silakan gunakan command /news \\<PAIR\\>\n"
            "Contoh: `/news BTC`",
            entities=[{"type": "bot_command", "offset": 24, "length": 5}]
        )
    elif data == "menu_portfolio":
        await myportfolio_command(update, context)
    elif data == "menu_signals":
        await mysignals_command(update, context)
    elif data == "menu_stats":
        await paperstats_command(update, context)
    elif data == "menu_help":
        await help_command(update, context)

    # --- TOMBOL REFRESH PRICE ---
    elif data.startswith("refresh_price_"):
        symbol = data.replace("refresh_price_", "")
        coin_id = SYMBOL_TO_COINGECKO_ID.get(symbol)
        if coin_id:
            try:
                price_data = await get_price(coin_id)
                message = format_price(price_data)
                await query.edit_message_text(
                    text=message,
                    parse_mode="Markdown",
                    reply_markup=price_keyboard(symbol)
                )
            except Exception as e:
                await query.answer("❌ Gagal memperbarui harga.")
                logger.error(f"Error refresh price: {e}")
        else:
            await query.answer("❌ Simbol tidak valid.")

    # --- TOMBOL REFRESH SIGNALS ---
    elif data == "refresh_signals":
        signals = get_open_signals(query.message.chat_id)
        if signals:
            now = datetime.utcnow()
            updated = []
            for sig in signals:
                sig = await check_and_update_signal(sig)
                if sig["status"] == "open":
                    try:
                        coin_id = SYMBOL_TO_COINGECKO_ID.get(sig["pair"])
                        if coin_id:
                            price_data = await get_price(coin_id)
                            sig["current_price"] = price_data.get("current_price")
                    except Exception:
                        sig["current_price"] = sig["entry_price"]

                    created_at = datetime.fromisoformat(sig["created_at"])
                    age = now - created_at
                    hours, remainder = divmod(int(age.total_seconds()), 3600)
                    minutes = remainder // 60
                    sig["age"] = f"{hours}j {minutes}m" if hours > 0 else f"{minutes}m"
                    updated.append(sig)

            if updated:
                message = format_signals(updated)
                await query.edit_message_text(
                    text=message,
                    parse_mode="Markdown",
                    reply_markup=signals_keyboard()
                )
            else:
                await query.edit_message_text(
                    text="📭 Semua sinyal sudah closed.",
                    reply_markup=signals_keyboard()
                )
        else:
            await query.edit_message_text(
                text="📭 Tidak ada sinyal aktif.",
                reply_markup=signals_keyboard()
            )

    # --- TOMBOL REFRESH PORTFOLIO ---
    elif data == "refresh_portfolio":
        positions = get_positions(query.message.chat_id)
        if positions:
            positions_data = []
            for pos in positions:
                pair = pos["pair"]
                side = pos["side"]
                entry = pos["entry_price"]
                amount = pos["amount"]
                try:
                    coin_id = SYMBOL_TO_COINGECKO_ID.get(pair)
                    if coin_id:
                        price_data = await get_price(coin_id)
                        current_price = price_data.get("current_price")
                        if current_price is None:
                            continue
                        pnl_pct = calculate_pnl(entry, current_price, side)
                        positions_data.append({
                            "id": pos["id"],
                            "pair": pair,
                            "side": side,
                            "entry_price": entry,
                            "current_price": current_price,
                            "pnl_pct": pnl_pct,
                            "amount": amount,
                        })
                except Exception:
                    pass

            if positions_data:
                message = format_portfolio(positions_data)
                await query.edit_message_text(
                    text=message,
                    parse_mode="Markdown",
                    reply_markup=portfolio_keyboard()
                )
            else:
                await query.edit_message_text(
                    text="⚠️ Gagal mengambil data harga.",
                    reply_markup=portfolio_keyboard()
                )
        else:
            await query.edit_message_text(
                text="📭 Kamu belum punya posisi aktif.",
                reply_markup=portfolio_keyboard()
            )

    # --- TOMBOL ANALYZE DARI PRICE ---
    elif data.startswith("analyze_"):
        symbol = data.replace("analyze_", "")
        await query.message.reply_text(f"Silakan ketik `/analyze {symbol} <TF> <KONDISI>` untuk analisis {symbol}.")

    # --- TOMBOL TAMBAH POSISI ---
    elif data == "add_position":
        await query.message.reply_text(
            "Gunakan `/addposition <PAIR> <long/short> <ENTRY> <AMOUNT>`\n"
            "Contoh: `/addposition BTC long 65000 0.01`"
        )

    # --- UNKNOWN ---
    else:
        await query.message.reply_text("❌ Tombol tidak dikenali.")

        