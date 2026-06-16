# bot/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Keyboard untuk /start — menu utama"""
    keyboard = [
        [InlineKeyboardButton("📈 Analyze", callback_data="menu_analyze"),
         InlineKeyboardButton("💰 Price", callback_data="menu_price")],
        [InlineKeyboardButton("📰 News", callback_data="menu_news"),
         InlineKeyboardButton("📊 Portfolio", callback_data="menu_portfolio")],
        [InlineKeyboardButton("📡 Signals", callback_data="menu_signals"),
         InlineKeyboardButton("📋 Stats", callback_data="menu_stats")],
        [InlineKeyboardButton("❓ Help", callback_data="menu_help")],
    ]
    return InlineKeyboardMarkup(keyboard)


def price_keyboard(symbol: str) -> InlineKeyboardMarkup:
    """Keyboard untuk /price — Refresh + Analyze"""
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_price_{symbol}"),
         InlineKeyboardButton(f"📈 Analyze {symbol}", callback_data=f"analyze_{symbol}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def analyze_keyboard() -> InlineKeyboardMarkup:
    """Keyboard untuk /analyze"""
    keyboard = [
        [InlineKeyboardButton("📡 Lihat Signals", callback_data="menu_signals"),
         InlineKeyboardButton("📊 Portfolio", callback_data="menu_portfolio")],
    ]
    return InlineKeyboardMarkup(keyboard)


def signals_keyboard() -> InlineKeyboardMarkup:
    """Keyboard untuk /mysignals"""
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh Signals", callback_data="refresh_signals")],
        [InlineKeyboardButton("📊 Menu Utama", callback_data="menu_start")],
    ]
    return InlineKeyboardMarkup(keyboard)


def portfolio_keyboard() -> InlineKeyboardMarkup:
    """Keyboard untuk /myportfolio"""
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_portfolio"),
         InlineKeyboardButton("➕ Tambah Posisi", callback_data="add_position")],
    ]
    return InlineKeyboardMarkup(keyboard)


def paperstats_keyboard() -> InlineKeyboardMarkup:
    """Keyboard untuk /paperstats"""
    keyboard = [
        [InlineKeyboardButton("📡 Lihat Signals", callback_data="menu_signals")],
        [InlineKeyboardButton("📊 Menu Utama", callback_data="menu_start")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Tombol kembali ke menu utama (untuk error/empty state)"""
    keyboard = [
        [InlineKeyboardButton("📊 Menu Utama", callback_data="menu_start")],
    ]
    return InlineKeyboardMarkup(keyboard)