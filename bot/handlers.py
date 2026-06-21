# bot/handlers.py
import json
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from services.coingecko import get_price, get_market_data
from services.llm import ask_llm
from services.news import get_news
from services.signals import save_signal, get_open_signals, check_and_update_signal, get_signal_stats
from db.database import init_db
from db.models import register_user, get_user_plan, set_user_plan, get_user
from utils.rate_limiter import check_and_increment, get_remaining
from utils.formatter import format_price, format_analyze, format_signals, format_paperstats, _wib_now
from utils.symbols import SYMBOL_TO_COINGECKO_ID, get_coin_id
from prompts.system import SYSTEM_PROMPT
from prompts.templates import build_analyze_prompt
from config import ADMIN_CHAT_ID
from bot.keyboards import (
    main_menu_keyboard, price_keyboard, analyze_keyboard, analyze_result_keyboard,
    signals_keyboard, paperstats_keyboard, back_to_menu_keyboard,
    pair_selection_keyboard, price_pair_selection_keyboard,
    news_pair_selection_keyboard, 
)
from services.scanner import scan_market
from utils.formatter import format_scan_result
from utils.validator import inject_calculated_prices, validate_signal_prices
from services.signals import has_open_signal
from services.signals import count_open_signals
from utils.rate_limiter import check_and_increment, get_remaining, MAX_OPEN_SIGNALS
from db.models import get_user_counts_by_plan, get_total_user_count, get_new_users_today
from services.signals import get_signal_summary, get_today_activity

# ==================== START ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    init_db()

    from db.models import is_new_user, get_user_plan
    new_user = is_new_user(chat_id)

    if new_user:
        register_user(chat_id, user.username, user.first_name)
        msg = (
            f"👋 Selamat datang di Crypto Prime, {user.first_name}!\n\n"
            "Aku AI trading assistant khusus futures crypto.\n"
            "Tiap analisa aku gabungin 3 hal sekaligus:\n"
            "📊 Pergerakan harga & tren\n"
            "📰 Berita & sentimen pasar\n"
            "💧 Likuiditas & keamanan\n\n"
            "Hasilnya: rekomendasi LONG/SHORT yang jelas,\n"
            "lengkap dengan Entry, Target, dan Stop Loss.\n"
            "Bukan tebak-tebakan — semua berbasis data real-time.\n\n"
            "🎁 Kamu dapat 3x /analyze gratis per hari.\n\n"
            "Coba sekarang 👇"
        )
    else:
        plan = get_user_plan(chat_id)
        plan_label = {"free": "Free", "premium": "Premium", "elite": "Elite", "admin": "Admin"}.get(plan, "Free")
        msg = (
            f"👋 Halo lagi {user.first_name}!\n\n"
            f"📡 Plan: {plan_label}\n\n"
            "Ketik /help untuk semua perintah."
        )

    await update.effective_message.reply_text(msg, reply_markup=main_menu_keyboard())


async def run_price(pair: str) -> tuple[str, InlineKeyboardMarkup]:
    """Logic inti /price, reusable."""
    coin_id = get_coin_id(pair)
    if not coin_id:
        return (f"❌ Pair {pair} tidak ditemukan.", back_to_menu_keyboard())

    try:
        price_data = await get_price(coin_id)
        result_text = format_price(price_data)
        keyboard = price_keyboard(pair)
        return (result_text, keyboard)
    except Exception as e:
        logger.error(f"Error run_price: {e}")
        return (f"❌ Gagal mengambil data untuk {pair}. Coba lagi.", back_to_menu_keyboard())


# ==================== PRICE ====================
async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            "💰 *Pilih pair untuk cek harga:*\n\n"
            "Tap salah satu di bawah, atau ketik pair lain.",
            parse_mode="Markdown",
            reply_markup=price_pair_selection_keyboard()
        )
        return

    pair = context.args[0].upper()
    result_text, keyboard = await run_price(pair)
    await update.effective_message.reply_text(
        result_text,
        parse_mode="Markdown",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )


async def run_analyze(pair: str, chat_id: int) -> tuple[str, InlineKeyboardMarkup]:
    """
    Logic inti analisa, reusable.
    Return (result_text, keyboard) siap dikirim/edit.
    """
    coin_id = get_coin_id(pair)
    if not coin_id:
        return (f"❌ Pair {pair} tidak ditemukan.", back_to_menu_keyboard())

    try:
        price_data = await get_market_data(coin_id)
    except Exception:
        basic = await get_price(coin_id)
        price_data = {
            "current_price": basic.get("current_price"),
            "price_change_24h": basic.get("price_change_percentage_24h", 0) or 0,
            "price_change_7d": 0,
            "total_volume": basic.get("total_volume"),
            "market_cap": basic.get("market_cap"),
            "high_24h": None,
            "low_24h": None,
        }

    articles = await get_news(pair)
    headlines = [a["title"] for a in articles[:5]]
    prompt = build_analyze_prompt(pair, price_data, headlines)
    raw = await ask_llm(SYSTEM_PROMPT, prompt)

    try:
        data = json.loads(raw)
         # Hitung target_price & stop_loss matematis
        data = inject_calculated_prices(data)
    except json.JSONDecodeError:
        return (raw, back_to_menu_keyboard())

    is_valid = validate_signal_prices(data, price_data["current_price"])
    if data.get("verdict") == "SETUP_VALID" and not is_valid:
        data["verdict"] = "NO_SETUP"
        data["verdict_reason"] = "Setup ditolak: entry tidak realistis atau R:R kurang."

    if data.get("verdict") == "SETUP_VALID" and is_valid:
        plan = get_user_plan(chat_id)
        max_signals = MAX_OPEN_SIGNALS.get(plan, 5)
        current_count = count_open_signals(chat_id)

        if current_count >= max_signals:
            data["duplicate_note"] = (
                f"⚠️ Kamu sudah mencapai limit {max_signals} open signal "
                f"untuk plan {plan}. Signal ini TIDAK disimpan. "
                f"Tunggu signal lain closed atau upgrade plan."
            )
        elif has_open_signal(chat_id, pair):
            data["duplicate_note"] = (
                f"ℹ️ Kamu sudah punya open signal untuk {pair}. "
                f"Signal baru ini TIDAK disimpan ke /mysignals."
            )
        else:
            save_signal(
                chat_id,
                pair + "/USDT",
                data["side"].lower(),
                float(data["entry_price"]),
                float(data["target_price"]),
                float(data["stop_loss"]),
            )

    result_text = format_analyze(data, pair, price_data)
    keyboard = analyze_result_keyboard(pair)
    return (result_text, keyboard)


# ==================== ANALYZE ====================
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    plan = get_user_plan(chat_id)

    if not check_and_increment(chat_id, "analyze", plan):
        plan_label = {"free": "Free (3x/hari)", "premium": "⭐ Premium", "elite": "👑 Elite", "admin": "👑 Admin"}.get(plan, "Free")
        await update.effective_message.reply_text(
            f"⛔ Kuota /analyze kamu habis hari ini (plan {plan_label}).\nUpgrade ke Premium untuk kuota lebih banyak.\nReset: 00:00 UTC"
        )
        return

    if not context.args:
        await update.effective_message.reply_text(
            "📊 *Pilih pair untuk dianalisis:*\n\nTap salah satu di bawah, atau ketik pair lain.",
            parse_mode="Markdown",
            reply_markup=pair_selection_keyboard(),
        )
        return

    pair = context.args[0].upper()
    await update.effective_message.reply_text("🔍 Menganalisis multi-factor... Mohon tunggu.")

    result_text, keyboard = await run_analyze(pair, chat_id)

    await update.effective_message.reply_text(
        result_text,
        parse_mode="Markdown",
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


# ==================== NEWS ====================
async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    plan = get_user_plan(chat_id)

    if not check_and_increment(chat_id, "news", plan):
        plan_label = {"free": "Free (5x/hari)", "premium": "⭐ Premium", "elite": "👑 Elite", "admin": "👑 Admin"}.get(plan, "Free")
        await update.effective_message.reply_text(
            f"⛔ Kuota /news kamu habis hari ini (plan {plan_label}).\nUpgrade ke Premium untuk kuota lebih banyak.\nReset: 00:00 UTC"
        )
        return

    if not context.args:
        await update.effective_message.reply_text(
            "📰 *Pilih pair untuk cek berita:*\n\nTap salah satu di bawah, atau ketik pair lain.",
            parse_mode="Markdown",
            reply_markup=news_pair_selection_keyboard()
        )
        return

    pair = context.args[0].upper()
    await update.effective_message.reply_text(f"📰 Mencari berita terkini untuk *{pair}*...")

    try:
        articles = await get_news(pair)
        if not articles:
            await update.effective_message.reply_text(f"😔 Tidak ada berita terkini untuk *{pair}*.", reply_markup=back_to_menu_keyboard())
            return

        summary = f"📰 *Berita Terkini — {pair}*\n\n"
        for i, article in enumerate(articles, 1):
            title = article.get("title", "No title")
            source = article.get("source", "Unknown")
            summary += f"{i}. *{title}*\n   Sumber: {source}\n\n"
        await update.effective_message.reply_text(summary, parse_mode="Markdown")

        articles_text = "\n".join([f"- {a.get('title', '')} ({a.get('source', '')})" for a in articles])
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


# ==================== SIGNALS & STATS ====================
async def mysignals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    signals = get_open_signals(chat_id)
    if not signals:
        await update.effective_message.reply_text(
            "📭 Kamu belum punya sinyal aktif.\nGunakan `/analyze` untuk dapat rekomendasi trading.",
            reply_markup=signals_keyboard(),
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
                f"telah {sig['status'].replace('_', ' ').title()}! P&L: {sig.get('result_pct', 0):+.2f}%"
            )
            continue

        try:
            coin_id = get_coin_id(sig["pair"])
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
        msg = format_signals(updated_signals)
        await update.effective_message.reply_text(msg, parse_mode="Markdown", reply_markup=signals_keyboard())
    else:
        await update.effective_message.reply_text(
            "📭 Semua sinyal sudah closed. Gunakan `/analyze` untuk dapat sinyal baru.",
            reply_markup=signals_keyboard(),
        )


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
            "📭 Belum ada sinyal tercatat.\nGunakan `/analyze` untuk dapat rekomendasi trading.",
            reply_markup=paperstats_keyboard(),
        )
        return

    msg = format_paperstats(stats)
    await update.effective_message.reply_text(msg, parse_mode="Markdown", reply_markup=paperstats_keyboard())


# ==================== PLAN & UPGRADE ====================
async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    plan = get_user_plan(chat_id)
    remaining = get_remaining(chat_id, plan)

    plan_label = {"free": "🆓 Free", "premium": "⭐ Premium", "elite": "👑 Elite", "admin": "👑 Admin"}.get(plan, "Free")
    analyze_display = "Unlimited" if plan in ("elite", "admin") else f"{remaining['analyze_remaining']}x"
    news_display = "Unlimited" if plan in ("elite", "admin") else f"{remaining['news_remaining']}x"

    expiry_info = ""
    if plan not in ("free", "admin"):
        user = get_user(chat_id)
        expiry_str = user.get("plan_expiry") if user else None
        if expiry_str:
            try:
                expiry = datetime.fromisoformat(expiry_str)
                now = datetime.utcnow()
                remaining_days = (expiry - now).days
                if remaining_days < 0:
                    remaining_days = 0
                expiry_info = f"⏳ Sisa {remaining_days} hari\n\n"
            except Exception:
                pass

    message = (
        f"📊 *Kuota Harian Kamu*\n\n"
        f"Plan: {plan_label}\n\n"
        f"{expiry_info}"
        f"🔍 /analyze : {analyze_display} tersisa\n"
        f"📰 /news    : {news_display} tersisa\n\n"
        "Kuota di-reset setiap hari pukul 00:00 UTC."
    )
    await update.effective_message.reply_text(message, parse_mode="Markdown", reply_markup=back_to_menu_keyboard())


async def upgrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "🚀 *Crypto Prime — Upgrade Plan*\n\n"
        "Buka potensi trading maksimal dengan AI analisis tanpa batas.\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⭐ *PRO-TRADER*\n"
        "💰 Rp 250.000 / bulan\n\n"
        "✅ 30x /analyze per hari\n✅ 50x /news per hari\n"
        "✅ Analisis multi-factor (Teknikal, Sentimen, Likuiditas)\n"
        "✅ Scan Market (/scan) — cari setup LAYAK dari 100 pair\n"
        "✅ Sinyal otomatis tersimpan\n✅ Support prioritas\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "👑 *ELITE (Most Powerful)*\n"
        "💰 Rp 500.000 / bulan\n\n"
        "✅ Unlimited /analyze & /news\n"
        "✅ Analisis AI paling akurat & mendalam\n"
        "✅ Scan Market + Auto Broadcast Signal tiap 4 jam\n"
        "✅ Notifikasi real-time\n✅ Paper trading stats + Sinyal tracker\n"
        "✅ Support VIP 1-on-1\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📞 *Cara Upgrade:*\nHubungi admin: @BenzAckerman\n"
        "Pembayaran via QRIS / Transfer Bank\n\n"
        "💡 *Kenapa upgrade?*\n• Akurasi sinyal lebih tinggi\n"
        "• Akses fitur eksklusif (Scan Market, Auto Broadcast)\n"
        "• Kuota unlimited untuk analisis harian\n• Dukung pengembangan bot ini\n\n"
        "⚠️ *Catatan:* Hasil trading bergantung pada kondisi pasar. "
        "Bot ini alat bantu analisis, bukan jaminan profit."
    )
    await update.effective_message.reply_text(message, parse_mode="Markdown", reply_markup=back_to_menu_keyboard())


async def setplan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller_id = update.effective_user.id
    if caller_id != ADMIN_CHAT_ID:
        await update.effective_message.reply_text("⛔ Kamu tidak punya akses command ini.")
        return

    if not context.args or len(context.args) < 2:
        await update.effective_message.reply_text(
            "⚠️ Format: `/setplan <chat_id> <plan> [days]`\n"
            "Plan: free, premium, elite, admin\n"
            "Contoh: `/setplan 123456789 premium 30` (30 hari)\nKosongkan days untuk permanen."
        )
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("❌ Chat ID harus angka.")
        return

    plan = context.args[1].lower()
    days = None
    if len(context.args) >= 3:
        try:
            days = int(context.args[2])
        except ValueError:
            await update.effective_message.reply_text("❌ Durasi harus angka (hari).")
            return

    success = set_user_plan(target_id, plan, days)
    if success:
        if days:
            await update.effective_message.reply_text(
                f"✅ User `{target_id}` berhasil diset ke plan: *{plan}* selama {days} hari.", parse_mode="Markdown"
            )
        else:
            await update.effective_message.reply_text(
                f"✅ User `{target_id}` berhasil diset ke plan: *{plan}* (permanen).", parse_mode="Markdown"
            )
    else:
        await update.effective_message.reply_text("❌ Gagal. Plan tidak valid.")


async def userinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller_id = update.effective_user.id
    if caller_id != ADMIN_CHAT_ID:
        await update.effective_message.reply_text("⛔ Akses khusus admin.")
        return

    if not context.args:
        await update.effective_message.reply_text("⚠️ `/userinfo <chat_id>`")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("❌ Chat ID harus angka.")
        return

    user = get_user(target_id)
    if not user:
        await update.effective_message.reply_text("❌ User tidak ditemukan.")
        return

    plan = user.get("plan", "free")
    expiry = user.get("plan_expiry")
    first_name = user.get("first_name", "-")
    username = user.get("username", "-")

    expiry_str = expiry if expiry else "Permanen"
    msg = (
        f"👤 *User Info*\n\n"
        f"🔹 Nama: {first_name}\n🔹 Username: @{username}\n"
        f"🔹 Chat ID: `{target_id}`\n🔹 Plan: {plan}\n🔹 Expiry: {expiry_str}"
    )
    await update.effective_message.reply_text(msg, parse_mode="Markdown")


async def adminstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_user.id

    if chat_id != ADMIN_CHAT_ID:
        await update.effective_message.reply_text("⛔ Kamu tidak punya akses command ini.")
        return

    plan_counts = get_user_counts_by_plan()
    total_users = get_total_user_count()
    new_today = get_new_users_today()
    signal_summary = get_signal_summary()
    activity = get_today_activity()

    text = (
        f"📊 *Admin Stats — Crypto Prime*\n"
        f"_{_wib_now().strftime('%H:%M WIB, %d %b %Y')}_\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 *User*\n"
        f"Total: {total_users} | Baru hari ini: +{new_today}\n\n"
        f"🆓 Free     : {plan_counts['free']}\n"
        f"⭐ Premium  : {plan_counts['premium']}\n"
        f"💎 Elite    : {plan_counts['elite']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 *Sinyal Paper Trading*\n"
        f"Open    : {signal_summary['total_open']}\n"
        f"Closed  : {signal_summary['total_closed']}\n"
        f"Win/Loss: {signal_summary['win_count']}/{signal_summary['loss_count']}\n"
        f"Win Rate: {signal_summary['win_rate']}%\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 *Aktivitas Hari Ini*\n"
        f"/analyze : {activity['analyze_count']}x\n"
        f"/news    : {activity['news_count']}x\n"
    )

    await update.effective_message.reply_text(text, parse_mode="Markdown")


async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    plan = get_user_plan(chat_id)

    if plan == "free":
        await update.effective_message.reply_text(
            "⛔ Fitur Scan Market hanya tersedia untuk plan Premium & Elite.\nKetik /upgrade untuk info paket."
        )
        return

    msg = await update.effective_message.reply_text("📡 Scanning top 100 pair...\nIni butuh 1-2 menit, mohon tunggu ⏳")

    try:
        signals = await scan_market(limit=100)
        result = format_scan_result(signals)
        await msg.edit_text(result, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error /scan: {e}")
        await msg.edit_text("😔 Gagal melakukan scan market. Coba lagi nanti.")


# ==================== HELP ====================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from utils.rate_limiter import PLAN_LIMITS, MAX_OPEN_SIGNALS

    help_text = f"""
🤖 *Crypto Prime — AI Trading Assistant*
_Futures crypto, dianalisa AI 24/7_

━━━━━━━━━━━━━━━━━━━━

🎯 *MULAI DI SINI*
/analyze — Analisa lengkap satu pair
/scan — Cari sinyal terbaik dari 100 pair _(Premium+)_

📊 *DATA & RISET*
/price — Harga real-time
/news — Berita & sentimen

📡 *PORTOFOLIO SINYAL*
/mysignals — Sinyal aktifmu sekarang
/paperstats — Performa & win rate

⭐ *AKUN KAMU*
/usage — Sisa kuota & plan kamu
/upgrade — Lihat paket Premium & Elite

━━━━━━━━━━━━━━━━━━━━

📋 *Plan & Limit*
🆓 Free     — {PLAN_LIMITS['free']['analyze']}x analisa/hari, {MAX_OPEN_SIGNALS['free']} sinyal aktif
⭐ Premium  — {PLAN_LIMITS['premium']['analyze']}x analisa/hari, {MAX_OPEN_SIGNALS['premium']} sinyal aktif, Scan Market
👑 Elite    — Unlimited, {MAX_OPEN_SIGNALS['elite']} sinyal aktif, Scan Market

━━━━━━━━━━━━━━━━━━━━

⚠️ _Bot ini alat bantu analisa, bukan saran keuangan._
_Selalu DYOR sebelum trading._

📞 Admin: @BenzAckerman
"""
    await update.effective_message.reply_text(help_text, parse_mode="Markdown", reply_markup=back_to_menu_keyboard())


async def handle_pair_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tangkap pesan teks setelah user klik Ketik Pair Lain (analyze / price / news)."""

    # --- Analyze ---
    if context.user_data.get("awaiting_pair_input"):
        pair = update.message.text.strip().upper()
        context.user_data["awaiting_pair_input"] = False
        if not pair:
            await update.effective_message.reply_text("❌ Pair tidak boleh kosong.")
            return
        await update.effective_message.reply_text(f"🔍 Menganalisis {pair}... Mohon tunggu.")
        result_text, keyboard = await run_analyze(pair, update.effective_chat.id)
        await update.effective_message.reply_text(
            result_text, parse_mode="Markdown", reply_markup=keyboard, disable_web_page_preview=True
        )
        return

    # --- Price ---
    if context.user_data.get("awaiting_price_input"):
        pair = update.message.text.strip().upper()
        context.user_data["awaiting_price_input"] = False
        if not pair:
            await update.effective_message.reply_text("❌ Pair tidak boleh kosong.")
            return
        result_text, keyboard = await run_price(pair)
        await update.effective_message.reply_text(
            result_text, parse_mode="Markdown", reply_markup=keyboard, disable_web_page_preview=True
        )
        return

    # --- News ---
    if context.user_data.get("awaiting_news_input"):
        pair = update.message.text.strip().upper()
        context.user_data["awaiting_news_input"] = False
        if not pair:
            await update.effective_message.reply_text("❌ Pair tidak boleh kosong.")
            return
        try:
            articles = await get_news(pair)
            if not articles:
                await update.effective_message.reply_text(
                    f"❌ Tidak ada berita untuk {pair}.", reply_markup=back_to_menu_keyboard()
                )
                return
            summary = f"📰 *Berita Terkini — {pair}*\n\n"
            for i, article in enumerate(articles, 1):
                title = article.get("title", "No title")
                source = article.get("source", "Unknown")
                summary += f"{i}. *{title}*\n   Sumber: {source}\n\n"
            articles_text = "\n".join([f"- {a.get('title', '')}" for a in articles])
            sentiment_prompt = (
                f"Analisis sentimen berita berikut untuk {pair}. "
                f"Klasifikasikan sebagai Bullish 🟢, Bearish 🔴, atau Neutral ⚪, "
                f"dan beri penjelasan singkat (2-3 kalimat):\n\n{articles_text}"
            )
            sentiment = await ask_llm(SYSTEM_PROMPT, sentiment_prompt)
            summary += f"\n📊 *Sentimen:* {sentiment}"
            await update.effective_message.reply_text(
                summary, parse_mode="Markdown", reply_markup=back_to_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Error awaiting_news_input: {e}")
            await update.effective_message.reply_text(
                "❌ Gagal mengambil berita.", reply_markup=back_to_menu_keyboard()
            )
        return

    # Tidak ada flag aktif → abaikan


# ==================== CALLBACKS ====================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # --- MENU UTAMA ---
    if data == "menu_start":
        await start_command(update, context)
    elif data == "menu_analyze":
        await query.message.reply_text(
            "Silakan gunakan command /analyze \\<PAIR\\>\nContoh: `/analyze BTC`",
            entities=[{"type": "bot_command", "offset": 24, "length": 8}],
        )
    elif data == "menu_price":
        await query.answer()
        await query.edit_message_text(
            "💰 *Pilih pair untuk cek harga:*\n\n"
            "Tap salah satu di bawah, atau ketik pair lain.",
            parse_mode="Markdown",
            reply_markup=price_pair_selection_keyboard()
        )
    elif data == "menu_news":
        await query.message.reply_text(
            "Silakan gunakan command /news \\<PAIR\\>\nContoh: `/news BTC`",
            entities=[{"type": "bot_command", "offset": 24, "length": 5}],
        )
    elif data == "menu_signals":
        await mysignals_command(update, context)
    elif data == "menu_stats":
        await paperstats_command(update, context)
    elif data == "menu_upgrade":
        await upgrade_command(update, context)
    elif data == "menu_profile":
        await usage_command(update, context)
    elif data == "menu_help":
        await help_command(update, context)
    elif data == "menu_scan":
        await scan_command(update, context)

    # --- REFRESH PRICE ---
    elif data.startswith("refresh_price_"):
        symbol = data.replace("refresh_price_", "")
        coin_id = get_coin_id(symbol)
        if coin_id:
            try:
                price_data = await get_price(coin_id)
                msg = format_price(price_data)
                await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=price_keyboard(symbol))
            except Exception as e:
                await query.answer("❌ Gagal memperbarui harga.")
                logger.error(f"Error refresh price: {e}")
        else:
            await query.answer("❌ Simbol tidak valid.")

    # --- REFRESH SIGNALS ---
    elif data == "refresh_signals":
        signals = get_open_signals(query.message.chat_id)
        if signals:
            now = datetime.utcnow()
            updated = []
            for sig in signals:
                sig = await check_and_update_signal(sig)
                if sig["status"] == "open":
                    try:
                        coin_id = get_coin_id(sig["pair"])
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
                msg = format_signals(updated)
                await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=signals_keyboard())
            else:
                await query.edit_message_text("📭 Semua sinyal sudah closed.", reply_markup=signals_keyboard())
        else:
            await query.edit_message_text("📭 Tidak ada sinyal aktif.", reply_markup=signals_keyboard())

    # --- REFRESH ANALYZE ---
    elif data.startswith("refresh_analyze_"):
        pair = data.replace("refresh_analyze_", "")
        await query.answer("🔄 Menganalisis ulang...")
        result_text, keyboard = await run_analyze(pair, query.message.chat_id)
        await query.edit_message_text(
            result_text, parse_mode="Markdown", reply_markup=keyboard, disable_web_page_preview=True
        )

    # --- PILIH PAIR DARI KEYBOARD ---
    elif data.startswith("analyze_pair_"):
        pair = data.replace("analyze_pair_", "")
        await query.answer(f"🔍 Menganalisis {pair}...")
        result_text, keyboard = await run_analyze(pair, query.message.chat_id)
        await query.edit_message_text(
            result_text, parse_mode="Markdown", reply_markup=keyboard, disable_web_page_preview=True
        )

    # --- KETIK PAIR LAIN ---
    elif data == "analyze_custom":
        await query.answer()
        await query.edit_message_text(
            "✏️ Ketik nama coin yang mau dianalisis:\n"
            "Contoh: SUI, ATOM, INJ, TIA",
        )
        from telegram import ForceReply
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="👇 Ketik di sini:",
            reply_markup=ForceReply(selective=True, input_field_placeholder="Contoh: SUI")
        )
        context.user_data["awaiting_pair_input"] = True

    # --- ANALYZE DARI PRICE --- (dipindah ke paling akhir agar tidak menangkap analyze_pair_)
    elif data.startswith("analyze_"):
        symbol = data.replace("analyze_", "")
        await query.answer(f"🔍 Menganalisis {symbol}...")
        result_text, keyboard = await run_analyze(symbol, query.message.chat_id)
        await query.edit_message_text(
            result_text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )

    elif query.data.startswith("price_pair_"):
        pair = query.data.replace("price_pair_", "")
        await query.answer(f"💰 Cek harga {pair}...")
        result_text, keyboard = await run_price(pair)
        await query.edit_message_text(
            result_text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )

    elif query.data == "price_custom":
        await query.answer()
        await query.edit_message_text(
            "✏️ Ketik nama coin yang mau dicek harganya:\nContoh: SUI, ATOM, INJ",
        )
        from telegram import ForceReply
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="👇 Ketik di sini:",
            reply_markup=ForceReply(selective=True, input_field_placeholder="Contoh: SUI")
        )
        context.user_data["awaiting_price_input"] = True    

    elif query.data.startswith("news_pair_"):
        pair = query.data.replace("news_pair_", "")
        await query.answer(f"📰 Mengambil berita {pair}...")
        try:
            articles = await get_news(pair)
            if not articles:
                await query.edit_message_text(f"❌ Tidak ada berita untuk {pair}.", reply_markup=back_to_menu_keyboard())
                return
            summary = f"📰 *Berita Terkini — {pair}*\n\n"
            for i, article in enumerate(articles, 1):
                title = article.get("title", "No title")
                source = article.get("source", "Unknown")
                summary += f"{i}. *{title}*\n   Sumber: {source}\n\n"
            articles_text = "\n".join([f"- {a.get('title', '')}" for a in articles])
            sentiment_prompt = f"Analisis sentimen berita berikut untuk {pair}. Klasifikasikan sebagai Bullish 🟢, Bearish 🔴, atau Neutral ⚪, dan beri penjelasan singkat (2-3 kalimat):\n\n{articles_text}"
            sentiment = await ask_llm(SYSTEM_PROMPT, sentiment_prompt)
            summary += f"\n📊 *Sentimen:* {sentiment}"
            await query.edit_message_text(summary, parse_mode="Markdown", reply_markup=back_to_menu_keyboard())
        except Exception as e:
            logger.error(f"Error news_pair_: {e}")
            await query.edit_message_text("❌ Gagal mengambil berita.", reply_markup=back_to_menu_keyboard())

    elif query.data == "news_custom":
        await query.answer()
        await query.edit_message_text("✏️ Ketik nama coin untuk cek berita:\nContoh: SUI, ATOM, INJ")
        from telegram import ForceReply
        await context.bot.send_message(chat_id=query.message.chat_id, text="👇 Ketik di sini:", reply_markup=ForceReply(selective=True, input_field_placeholder="Contoh: SUI"))
        context.user_data["awaiting_news_input"] = True    

    else:
        await query.message.reply_text("❌ Tombol tidak dikenali.")