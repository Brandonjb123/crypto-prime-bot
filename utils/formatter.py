# utils/formatter.py


def format_price(data: dict) -> str:
    """
    Format data harga dari CoinGecko menjadi pesan Telegram yang rapi.
    """
    name = data.get("name", "Unknown")
    symbol = data.get("symbol", "???")
    price = data.get("current_price")
    market_cap = data.get("market_cap")
    volume = data.get("total_volume")
    change = data.get("price_change_percentage_24h")

    # Emoji dan arah perubahan
    if change is not None:
        if change > 0:
            emoji = "🟢"
            direction = "naik"
        elif change < 0:
            emoji = "🔴"
            direction = "turun"
        else:
            emoji = "⚪"
            direction = "tetap"
        change_str = f"{emoji} {change:.2f}% ({direction})"
    else:
        change_str = "N/A"

    # Format angka dengan pemisah ribuan (kalau None, tampil "N/A")
    def usd(val):
        if val is None:
            return "N/A"
        return f"${val:,.2f}"

    message = (
        f"💰 *{name} ({symbol})*\n\n"
        f"💵 Harga: `{usd(price)}`\n"
        f"📈 24j: {change_str}\n"
        f"📊 Volume 24j: `{usd(volume)}`\n"
        f"🏦 Market Cap: `{usd(market_cap)}`\n\n"
        f"_Data: CoinGecko_"
    )
    return message