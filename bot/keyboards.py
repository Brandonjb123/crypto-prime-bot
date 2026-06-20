# bot/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📡 Scan Market", callback_data="menu_scan"),
         InlineKeyboardButton("💰 Price", callback_data="menu_price")],
        [InlineKeyboardButton("📰 News", callback_data="menu_news"),
         InlineKeyboardButton("🎯 Signals", callback_data="menu_signals")],
        [InlineKeyboardButton("📊 Stats", callback_data="menu_stats"),
         InlineKeyboardButton("👤 Profile", callback_data="menu_profile")],
        [InlineKeyboardButton("⭐ Upgrade", callback_data="menu_upgrade"),
         InlineKeyboardButton("❓ Help", callback_data="menu_help")],
    ]
    return InlineKeyboardMarkup(keyboard)

def price_keyboard(symbol: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_price_{symbol}"),
         InlineKeyboardButton(f"📈 Analyze {symbol}", callback_data=f"analyze_{symbol}")],
    ]
    return InlineKeyboardMarkup(keyboard)

def analyze_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📡 Lihat Signals", callback_data="menu_signals"),
         InlineKeyboardButton("📡 Scan Market", callback_data="menu_scan")],
    ]
    return InlineKeyboardMarkup(keyboard)

def analyze_result_keyboard(pair: str) -> InlineKeyboardMarkup:
    tv_symbol = pair.replace("/USDT", "USD").replace("USDT", "USD")
    keyboard = [
        [
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_analyze_{pair}"),
            InlineKeyboardButton("📊 Chart", url=f"https://www.tradingview.com/chart/?symbol={tv_symbol}")
        ],
        [
            InlineKeyboardButton("📡 Scan Market", callback_data="menu_scan"),
            InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_start")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def signals_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh Signals", callback_data="refresh_signals")],
        [InlineKeyboardButton("📊 Menu Utama", callback_data="menu_start")],
    ]
    return InlineKeyboardMarkup(keyboard)

def portfolio_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_portfolio"),
         InlineKeyboardButton("➕ Tambah Posisi", callback_data="add_position")],
    ]
    return InlineKeyboardMarkup(keyboard)

def paperstats_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📡 Lihat Signals", callback_data="menu_signals")],
        [InlineKeyboardButton("📊 Menu Utama", callback_data="menu_start")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📊 Menu Utama", callback_data="menu_start")],
    ]
    return InlineKeyboardMarkup(keyboard)

POPULAR_PAIRS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX"]

def pair_selection_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    row = []
    for i, pair in enumerate(POPULAR_PAIRS):
        row.append(InlineKeyboardButton(pair, callback_data=f"analyze_pair_{pair}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("✏️ Ketik Pair Lain", callback_data="analyze_custom")
    ])
    keyboard.append([
        InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_start")
    ])
    return InlineKeyboardMarkup(keyboard)

def price_pair_selection_keyboard() -> InlineKeyboardMarkup:
    """Tombol pilihan pair untuk /price tanpa argumen."""
    keyboard = []
    row = []
    for i, pair in enumerate(POPULAR_PAIRS):
        row.append(InlineKeyboardButton(pair, callback_data=f"price_pair_{pair}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("✏️ Ketik Pair Lain", callback_data="price_custom")
    ])
    keyboard.append([
        InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_start")
    ])
    return InlineKeyboardMarkup(keyboard)