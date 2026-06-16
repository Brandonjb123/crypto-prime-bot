# utils/formatter.py
from datetime import datetime

def format_price(data: dict) -> str:
    name = data.get("name", "Unknown")
    symbol = data.get("symbol", "???")
    price = data.get("current_price")
    change = data.get("price_change_percentage_24h")

    if change is not None:
        emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        change_str = f"{emoji} {change:+.2f}%"
    else:
        change_str = "N/A"

    usd = lambda val: f"${val:,.2f}" if val is not None else "N/A"
    
    message = (
        f"💰 *{name} ({symbol})*\n\n"
        f"Harga: `{usd(price)}`\n"
        f"24j: {change_str}\n"
        f"Volume: `{usd(data.get('total_volume'))}`\n"
        f"Market Cap: `{usd(data.get('market_cap'))}`\n\n"
        f"_Data: CoinGecko_"
    )
    message += f"\n🕐 *Diperbarui: {datetime.now().strftime('%H:%M:%S')} WIB*"
    return message


def format_analyze(data: dict) -> str:
    emoji_side = "🟢" if data["side"] == "long" else "🔴"
    side_str = f"{emoji_side} {data['side'].upper()}"
    
    entry = data["entry_price"]
    target = data["target_price"]
    stop = data["stop_loss"]
    
    reward = abs(target - entry)
    risk = abs(entry - stop)
    rr_ratio = f"1:{reward/risk:.1f}" if risk > 0 else "N/A"
    
    message = (
        f"📈 *Analisis {data['pair']}*\n\n"
        f"📍 Entry: `${entry:,.2f}`\n"
        f"🎯 Target: `${target:,.2f}` (+{(target/entry-1)*100:.2f}%)\n"
        f"🛑 Stop Loss: `${stop:,.2f}` (-{(entry/stop-1)*100:.2f}%)\n"
        f"📊 Side: {side_str}\n"
        f"⚖️ R/R Ratio: {rr_ratio}\n\n"
        f"📝 Ringkasan:\n{data.get('summary', 'N/A')}\n\n"
        f"⚠️ Risk Notes:\n{data.get('risk_notes', 'N/A')}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"⚠️ *Bukan financial advice. Trade dengan risiko sendiri.*"
    )
    return message


def format_signals(signals: list) -> str:
    if not signals:
        return "📭 Tidak ada sinyal aktif."
        
    message = f"📡 *Sinyal Aktif Kamu ({len(signals)})*\n\n"
    
    for sig in signals:
        side_emoji = "🟢" if sig["side"] == "long" else "🔴"
        entry = sig["entry_price"]
        current = sig.get("current_price", entry)
        pnl = ((current - entry) / entry * 100) if sig["side"] == "long" else ((entry - current) / entry * 100)
        pnl_emoji = "🟢" if pnl >= 0 else "🔴"
        
        message += (
            f"#{sig['id']} {side_emoji} *{sig['pair']}* {sig['side'].upper()}\n"
            f"Entry: ${entry:,.2f} → Now: ${current:,.2f} ({pnl_emoji} {pnl:+.2f}%)\n"
            f"Target: ${sig['target_price']:,.2f} | Stop: ${sig['stop_loss']:,.2f}\n"
            f"Umur: {sig.get('age', 'N/A')}\n\n"
        )
    
    message += f"🕐 *Diperbarui: {datetime.now().strftime('%H:%M:%S')} WIB*"
    return message


def format_portfolio(positions: list) -> str:
    if not positions:
        return "📭 Kamu belum punya posisi aktif."

    message = "📋 *Portfolio Kamu*\n\n"
    total_pnl = 0.0
    
    for pos in positions:
        emoji = "🟢" if pos["pnl_pct"] >= 0 else "🔴"
        message += (
            f"#{pos['id']} {emoji} *{pos['pair']}* {pos['side'].upper()}\n"
            f"Entry: ${pos['entry_price']:,.2f} → Now: ${pos['current_price']:,.2f}\n"
            f"P&L: {emoji} {pos['pnl_pct']:+.2f}% | Amount: {pos['amount']}\n\n"
        )
        total_pnl += pos["pnl_pct"]
    
    total_emoji = "🟢" if total_pnl >= 0 else "🔴"
    message += (
        f"━━━━━━━━━━━━━━\n"
        f"Total P&L: {total_emoji} {total_pnl:+.2f}%"
    )
    message += f"\n🕐 *Diperbarui: {datetime.now().strftime('%H:%M:%S')} WIB*"
    return message


def format_paperstats(stats: dict) -> str:
    message = "📊 *Paper Trading Stats*\n\n"
    message += f"📈 Win Rate: {stats.get('win_rate', 0):.1f}% ({stats.get('win_count', 0)}/{stats.get('total_closed', 0)})\n"
    message += f"💰 Avg Profit: 🟢 {stats.get('avg_profit', 0):+.2f}%\n"
    message += f"💸 Avg Loss: 🔴 {stats.get('avg_loss', 0):+.2f}%\n\n"
    message += f"📡 Open: {stats.get('open_count', 0)} sinyal aktif\n"
    message += f"✅ Closed: {stats.get('total_closed', 0)} sinyal\n\n"
    message += f"Model: llama-3.1-8b-instant\n"
    message += f"🕐 *Diperbarui: {datetime.now().strftime('%H:%M:%S')} WIB*"
    
    return message