"""Inline keyboards untuk Telegram UX."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

MAIN_MENU = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("📊 Sinyal Terkini", callback_data="menu_signals"),
        InlineKeyboardButton("💼 Portfolio", callback_data="menu_portfolio"),
    ],
    [
        InlineKeyboardButton("📈 Posisi", callback_data="menu_positions"),
        InlineKeyboardButton("📜 History", callback_data="menu_history"),
    ],
    [
        InlineKeyboardButton("📋 Track Record", callback_data="menu_trackrecord"),
        InlineKeyboardButton("⭐ Subscribe", callback_data="menu_subscribe"),
    ],
    [
        InlineKeyboardButton("❓ Bantuan", callback_data="menu_help"),
        InlineKeyboardButton("ℹ️ Status", callback_data="menu_status"),
    ],
])

BACK_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔙 Kembali", callback_data="menu_back")]
])

SIGNALS_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_signals")],
    [InlineKeyboardButton("🔙 Kembali", callback_data="menu_back")],
])

PORTFOLIO_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("💼 Portfolio", callback_data="menu_portfolio")],
    [InlineKeyboardButton("📈 Posisi", callback_data="menu_positions")],
    [InlineKeyboardButton("🔙 Kembali", callback_data="menu_back")],
])