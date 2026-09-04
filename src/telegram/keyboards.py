"""Inline keyboard builders."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

MAIN_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("📊 Market", callback_data="menu_market"),
     InlineKeyboardButton("📈 Signals", callback_data="menu_signals")],
    [InlineKeyboardButton("💼 Portfolio", callback_data="menu_portfolio"),
     InlineKeyboardButton("📋 Positions", callback_data="menu_positions")],
    [InlineKeyboardButton("📊 Performance", callback_data="menu_performance"),
     InlineKeyboardButton("⚙️ Status", callback_data="menu_status")],
    [InlineKeyboardButton("❓ Help", callback_data="menu_help")],
])

BACK_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("◀ Back", callback_data="menu_back")]
])