# utils/formatter.py
from datetime import datetime, timezone, timedelta

def _wib_now():
    """Return current time in WIB (UTC+7)."""
    return datetime.now(timezone.utc) + timedelta(hours=7)

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
    message += f"\n🕐 *Diperbarui: {_wib_now().strftime('%H:%M:%S')} WIB*"
    return message


def format_analyze(data: dict, pair: str, price_data: dict) -> str:
    verdict = data.get('verdict', 'TIDAK LAYAK')
    is_layak = verdict == 'LAYAK'

    # Teknikal section
    change_24h = price_data.get('price_change_24h', 0)
    change_7d = price_data.get('price_change_7d', 0)
    current_price = price_data.get('current_price', 0)
    teknikal = (
        f"📊 *Teknikal*\n"
        f"   Harga: ${current_price:,.6f}\n"
        f"   24h: {change_24h:+.1f}%  |  7d: {change_7d:+.1f}%\n"
        f"   Tren: {data.get('technical_bias', '-')}"
    )

    # Sentiment section
    sentiment = data.get('sentiment', 'Neutral')
    sent_icon = '✅' if sentiment == 'Positif' else ('⚠️' if sentiment == 'Negatif' else '➖')
    sentimen = f"📰 *Sentimen*\n   {sent_icon} {sentiment}"

    # Likuiditas section
    vol = price_data.get('total_volume', 0) or 0
    mcap = price_data.get('market_cap', 0) or 0
    likuiditas = (
        f"💧 *Likuiditas*\n"
        f"   Volume 24h: ${vol/1e6:.1f}M\n"
        f"   Mcap: ${mcap/1e9:.1f}B\n"
        f"   Status: {data.get('liquidity', '-')}"
    )

    # Verdict
    if is_layak:
        entry = data.get('entry_price')
        target = data.get('target_price')
        sl = data.get('stop_loss')
        rr = round((target - entry) / (entry - sl), 1) if sl and entry and target else '-'
        verdict_box = "✅ *VERDICT: LAYAK TRADING*"
        trade_section = (
            f"📐 *Setup Trade (4H)*\n"
            f"   Side    : {data.get('side', '-')}\n"
            f"   Entry   : ${entry:,.4f}\n"
            f"   Target  : ${target:,.4f}\n"
            f"   Stop    : ${sl:,.4f}\n"
            f"   R:R     : 1:{rr}\n\n"
            f"📝 {data.get('summary', '')}\n"
            f"⚠️ {data.get('risk_notes', 'DYOR, bukan financial advice')}"
        )
    else:
        verdict_box = "⛔ *VERDICT: TIDAK LAYAK*"
        trade_section = (
            f"Alasan: {data.get('verdict_reason', '-')}\n"
            f"Rekomendasi: Wait & see dulu"
        )

    # TradingView link — BTC/USDT → BTCUSD
    tv_pair = pair.replace("/USDT", "USD").replace("USDT", "USD")
    tv_link = f"https://www.tradingview.com/chart/?symbol={tv_pair}"

    return (
        f"🔍 *Analisa: {pair}*\n\n"
        f"{teknikal}\n\n"
        f"{sentimen}\n\n"
        f"{likuiditas}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{verdict_box}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{trade_section}\n\n"
        f"📈 Chart: {tv_link}"
    )


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
    
    message += f"🕐 *Diperbarui: {_wib_now().strftime('%H:%M:%S')} WIB*"
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
    message += f"\n🕐 *Diperbarui: {_wib_now().strftime('%H:%M:%S')} WIB*"
    return message


def format_paperstats(stats: dict) -> str:
    message = "📊 *Paper Trading Stats*\n\n"
    message += f"📈 Win Rate: {stats.get('win_rate', 0):.1f}% ({stats.get('win_count', 0)}/{stats.get('total_closed', 0)})\n"
    message += f"💰 Avg Profit: 🟢 {stats.get('avg_profit', 0):+.2f}%\n"
    message += f"💸 Avg Loss: 🔴 {stats.get('avg_loss', 0):+.2f}%\n\n"
    message += f"📡 Open: {stats.get('open_count', 0)} sinyal aktif\n"
    message += f"✅ Closed: {stats.get('total_closed', 0)} sinyal\n\n"
    message += f"Model: llama-3.1-8b-instant\n"
    message += f"🕐 *Diperbarui: {_wib_now().strftime('%H:%M:%S')} WIB*"
    
    return message