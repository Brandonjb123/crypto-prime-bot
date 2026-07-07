# utils/formatter.py
from datetime import datetime, timezone, timedelta
from utils.validator import REWARD_PERCENT, RISK_PERCENT

def _wib_now():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# Leverage tier per koin (kiblat Binance)
LEVERAGE_TIERS = {
    "BTC": 25, "ETH": 25, "BNB": 20, "XRP": 20,
    "SOL": 20, "ADA": 15, "DOGE": 15, "AVAX": 15,
    "LINK": 15, "DOT": 15, "MATIC": 15, "POL": 15,
    "LTC": 15, "UNI": 10, "ATOM": 10, "FIL": 10,
    "APT": 10, "ARB": 10, "OP": 10, "NEAR": 10,
    "INJ": 10, "SUI": 10, "TIA": 10, "SEI": 10,
    "PAXG": 10, "OKB": 10, "MNT": 10, "TAO": 10,
    "WIF": 10, "PEPE": 10, "SHIB": 10, "FLOKI": 5,
    "BONK": 5, "BOME": 5, "POPCAT": 5, "MEW": 5,
}

def get_recommended_leverage(symbol: str) -> int:
    sym = symbol.split("/")[0].upper()
    return LEVERAGE_TIERS.get(sym, 10)

def calculate_leverage_pnl(entry: float, target: float, stop: float, side: str, leverage: int = 10) -> dict:
    if side.upper() == "LONG":
        base_profit_pct = (target - entry) / entry * 100
        base_loss_pct = (entry - stop) / entry * 100
    else:
        base_profit_pct = (entry - target) / entry * 100
        base_loss_pct = (stop - entry) / entry * 100

    return {
        "profit": round(base_profit_pct * leverage, 1),
        "loss": round(base_loss_pct * leverage, 1),
        "leverage": leverage
    }

def format_leverage_estimate(entry: float, target: float, stop: float, side: str, symbol: str = "") -> str:
    lev = get_recommended_leverage(symbol)
    pnl = calculate_leverage_pnl(entry, target, stop, side, lev)
    return (
        f"⚙️ *Leverage Rekomendasi: {lev}x*\n"
        f"💡 Est. PnL @{lev}x:\n"
        f"   ✅ Profit: +{pnl['profit']}%\n"
        f"   ❌ Loss  : -{pnl['loss']}%\n"
        f"⚠️ _Leverage tinggi = risiko tinggi. DYOR._"
    )

def _smart_price(price):
    if price is None:
        return "N/A"
    if price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:,.4f}"
    elif price >= 0.01:
        return f"${price:,.6f}"
    else:
        return f"${price:,.8f}"

def _format_pair_display(pair: str) -> str:
    if "/" in pair:
        return pair
    return f"{pair}/USDT"

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

    return (
        f"💰 *{name} ({symbol.upper()})*\n\n"
        f"💵 Harga   : `{_smart_price(price)}`\n"
        f"📈 24h     : {change_str}\n"
        f"📦 Volume  : `{_smart_price(data.get('total_volume'))}`\n"
        f"🏦 Mcap    : `{_smart_price(data.get('market_cap'))}`\n\n"
        f"🕐 {_wib_now().strftime('%H:%M:%S')} WIB · CoinGecko"
    )

def format_analyze(data: dict, pair: str, price_data: dict) -> str:
    verdict = data.get('verdict', 'NO_SETUP')
    is_valid = verdict == 'SETUP_VALID'
    display_pair = _format_pair_display(pair)
    symbol = pair.split("/")[0].upper()

    change_24h = price_data.get('price_change_24h', 0) or 0
    change_7d = price_data.get('price_change_7d', 0) or 0
    current_price = price_data.get('current_price', 0) or 0
    vol = price_data.get('total_volume', 0) or 0
    mcap = price_data.get('market_cap', 0) or 0

    tren = "📈 Bullish" if change_24h > 1 else ("📉 Bearish" if change_24h < -1 else "➡️ Sideways")
    liq_status = ("🟢 Tinggi" if vol >= 1_000_000_000 else
                  "🟡 Sedang" if vol >= 100_000_000 else
                  "🟠 Rendah" if vol >= 1_000_000 else "🔴 Sangat Rendah")

    side = data.get('side')
    sent_icon = '🟢' if side == 'LONG' else ('🔴' if side == 'SHORT' else '⚪')
    sentiment = 'Bullish' if side == 'LONG' else ('Bearish' if side == 'SHORT' else 'Neutral')

    header = f"🔍 *ANALISA {display_pair}*\n"
    header += f"🕐 {_wib_now().strftime('%H:%M')} WIB\n"
    header += "━━━━━━━━━━━━━━━━━━━━\n\n"

    market_info = (
        f"📊 *Market Overview*\n"
        f"💵 Harga  : {_smart_price(current_price)}\n"
        f"📈 24h    : {change_24h:+.1f}%  |  7d: {change_7d:+.1f}%\n"
        f"📉 Tren   : {tren}\n"
        f"💬 Sentimen: {sent_icon} {sentiment}\n"
        f"💧 Likuiditas: {liq_status}\n"
        f"📦 Volume : ${vol/1e6:.1f}M\n\n"
    )

    if is_valid:
        entry = data.get('entry_price')
        target = data.get('target_price')
        sl = data.get('stop_loss')
        rr_display = round(REWARD_PERCENT / RISK_PERCENT, 1)
        reasoning = data.get('reasoning', '')
        lev = get_recommended_leverage(symbol)
        pnl = calculate_leverage_pnl(entry, target, sl, side, lev)

        verdict_section = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *SETUP VALID — TRADE READY*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{'🟢' if side == 'LONG' else '🔴'} *{side}*\n\n"
            f"📍 Entry  : {_smart_price(entry)}\n"
            f"🎯 Target : {_smart_price(target)}\n"
            f"🛑 Stop   : {_smart_price(sl)}\n"
            f"📊 R:R    : 1:{rr_display}\n\n"
            f"⚙️ *Leverage Rekomendasi: {lev}x*\n"
            f"   ✅ Est. Profit: +{pnl['profit']}%\n"
            f"   ❌ Est. Loss  : -{pnl['loss']}%\n\n"
            f"📝 _{reasoning}_\n\n"
            f"⚠️ Bukan financial advice. DYOR."
        )
    else:
        reason = data.get('verdict_reason') or data.get('reasoning', 'Kondisi market tidak ideal.')
        verdict_section = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🚫 *NO SETUP — SKIP DULU*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 _{reason}_\n\n"
            f"💡 Rekomendasi: Wait & see dulu."
        )

    tv_pair = display_pair.replace("/USDT", "USD")
    tv_link = f"https://www.tradingview.com/chart/?symbol={tv_pair}"

    result = header + market_info + verdict_section + f"\n\n📈 Chart: {tv_link}"
    if data.get("duplicate_note"):
        result += f"\n\n{data['duplicate_note']}"
    return result

def format_signals(signals: list) -> str:
    if not signals:
        return "📭 Tidak ada sinyal aktif."

    message = f"📡 *SINYAL AKTIF ({len(signals)})*\n"
    message += f"🕐 {_wib_now().strftime('%H:%M')} WIB\n"
    message += "━━━━━━━━━━━━━━━━━━━━\n\n"

    for sig in signals:
        side = sig["side"]
        side_emoji = "🟢" if side == "long" else "🔴"
        entry = sig["entry_price"]
        current = sig.get("current_price", entry)
        pnl = ((current - entry) / entry * 100) if side == "long" else ((entry - current) / entry * 100)
        pnl_emoji = "🟢" if pnl >= 0 else "🔴"
        display_pair = _format_pair_display(sig['pair'])
        symbol = sig['pair'].split("/")[0]
        lev = get_recommended_leverage(symbol)
        pnl_lev = round(pnl * lev, 1)

        message += (
            f"{side_emoji} *{display_pair}* — {side.upper()}\n"
            f"📍 Entry : {_smart_price(entry)}\n"
            f"💵 Now   : {_smart_price(current)} ({pnl_emoji} {pnl:+.2f}%)\n"
            f"🎯 Target: {_smart_price(sig['target_price'])}\n"
            f"🛑 Stop  : {_smart_price(sig['stop_loss'])}\n"
            f"⚙️ @{lev}x : {pnl_emoji} {pnl_lev:+.1f}%\n"
            f"⏱ Umur  : {sig.get('age', 'N/A')}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
        )

    return message

def format_paperstats(stats: dict) -> str:
    win_rate = stats.get('win_rate', 0)
    win_count = stats.get('win_count', 0)
    total_closed = stats.get('total_closed', 0)
    avg_profit_base = stats.get('avg_profit', 0)
    avg_loss_base = stats.get('avg_loss', 0)

    # Kalikan dengan leverage 10x untuk display
    avg_profit_10x = avg_profit_base * 10
    avg_loss_10x = avg_loss_base * 10

    wr_emoji = "🔥" if win_rate >= 60 else ("⚠️" if win_rate >= 40 else "📉")

    return (
        f"📊 *PAPER TRADING STATS*\n"
        f"🕐 {_wib_now().strftime('%H:%M')} WIB\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{wr_emoji} Win Rate  : *{win_rate:.1f}%* ({win_count}/{total_closed})\n\n"
        f"💰 Avg Profit @10x : 🟢 *+{avg_profit_10x:.1f}%*\n"
        f"💸 Avg Loss @10x   : 🔴 *-{abs(avg_loss_10x):.1f}%*\n\n"
        f"📡 Open   : {stats.get('open_count', 0)} sinyal aktif\n"
        f"✅ Closed : {total_closed} sinyal\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ _Basis simulasi leverage 10x. Bukan financial advice._"
    )

def format_scan_result(signals: list) -> str:
    if not signals:
        return (
            "📡 *Scan Market Selesai*\n\n"
            "❌ Tidak ada SETUP VALID saat ini.\n"
            "💡 Coba lagi dalam beberapa jam."
        )

    rr_display = round(REWARD_PERCENT / RISK_PERCENT, 1)
    lines = [
        f"📡 *SCAN MARKET — {len(signals)} SETUP VALID*\n"
        f"🕐 {_wib_now().strftime('%H:%M')} WIB\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    ]

    for i, s in enumerate(signals, 1):
        entry = s.get("entry_price", 0)
        target = s.get("target_price", 0)
        sl = s.get("stop_loss", 0)
        side = s.get("side", "-").upper()
        pair = s.get("pair", "-")
        display_pair = _format_pair_display(pair)
        symbol = pair.split("/")[0]
        side_icon = "🟢" if side == "LONG" else "🔴"
        lev = get_recommended_leverage(symbol)
        pnl = calculate_leverage_pnl(entry, target, sl, side, lev)

        lines.append(
            f"\n{i}. {side_icon} *{display_pair}* — {side}\n"
            f"   📍 Entry  : {_smart_price(entry)}\n"
            f"   🎯 Target : {_smart_price(target)}\n"
            f"   🛑 Stop   : {_smart_price(sl)}\n"
            f"   📊 R:R    : 1:{rr_display}\n"
            f"   ⚙️ @{lev}x  : +{pnl['profit']}% / -{pnl['loss']}%\n"
        )

    lines.append("\n━━━━━━━━━━━━━━━━━━━━")
    lines.append("⚠️ Bukan financial advice. DYOR.")
    return "\n".join(lines)

def format_broadcast_signal(signal: dict) -> str:
    pair = signal.get("pair", "-")
    display_pair = _format_pair_display(pair)
    symbol = pair.split("/")[0]
    side = signal.get("side", "-").upper()
    entry = signal.get("entry_price", 0)
    target = signal.get("target_price", 0)
    sl = signal.get("stop_loss", 0)
    reasoning = signal.get("reasoning", signal.get("summary", ""))
    side_icon = "🟢" if side == "LONG" else "🔴"
    rr_display = round(REWARD_PERCENT / RISK_PERCENT, 1)
    lev = get_recommended_leverage(symbol)
    pnl = calculate_leverage_pnl(entry, target, sl, side, lev)

    return (
        f"🚨 *VIP SIGNAL — {display_pair}*\n"
        f"🕐 {_wib_now().strftime('%H:%M')} WIB\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{side_icon} *{side}*\n\n"
        f"📍 Entry  : {_smart_price(entry)}\n"
        f"🎯 Target : {_smart_price(target)}\n"
        f"🛑 Stop   : {_smart_price(sl)}\n"
        f"📊 R:R    : 1:{rr_display}\n\n"
        f"⚙️ *Leverage Rekomendasi: {lev}x*\n"
        f"   ✅ Est. Profit: +{pnl['profit']}%\n"
        f"   ❌ Est. Loss  : -{pnl['loss']}%\n\n"
        f"📝 _{reasoning}_\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ Bukan financial advice. DYOR.\n"
        f"🤖 Crypto Prime AI Signal"
    )

def format_signal_closed(result: dict) -> str:
    pair = result["pair"]
    side = result["side"]
    result_type = result["result"]
    entry = result["entry_price"]
    close_price = result["close_price"]
    result_pct = result["result_pct"]
    symbol = pair.split("/")[0]
    lev = get_recommended_leverage(symbol)
    side_icon = "🟢" if side.upper() == "LONG" else "🔴"
    pnl_lev = result_pct * lev

    if result_type == "TP":
        return (
            f"🎯 *TARGET HIT — {pair}*\n\n"
            f"{side_icon} Side   : {side.upper()}\n"
            f"📍 Entry  : {_smart_price(entry)}\n"
            f"✅ Closed : {_smart_price(close_price)}\n"
            f"📊 Result : +{result_pct:.2f}%\n"
            f"⚙️ @{lev}x   : +{pnl_lev:.1f}%\n\n"
            f"🎉 Profit! Cek /paperstats."
        )
    else:
        return (
            f"🛑 *STOP LOSS HIT — {pair}*\n\n"
            f"{side_icon} Side   : {side.upper()}\n"
            f"📍 Entry  : {_smart_price(entry)}\n"
            f"🛑 Closed : {_smart_price(close_price)}\n"
            f"📊 Result : {result_pct:.2f}%\n"
            f"⚙️ @{lev}x   : {pnl_lev:.1f}%\n\n"
            f"📉 Loss. Cek /paperstats."
        )